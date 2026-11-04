"""Checkpoint interventions using the existing finite training engine.

Only the frozen mask and target provider change. All updates, including the
preconditioner and the special initial step, execute in fit_full.
"""
from dataclasses import replace

import numpy as np
import torch

from src.algorithms import SelfTrainedGradientDescent
from src.initialization import SelfTrainingInitialization, compute_scores, sign_with_positive_tie
from src.objectives import LogisticLoss
from src.performance import population_error


def configuration(scores, kappa_minus, kappa_plus):
    """Inclusive selected boundaries; the interior zero interval is open."""
    return torch.where(scores <= kappa_minus, -1, torch.where(scores >= kappa_plus, 1, 0))


class FrozenTargets(LogisticLoss):
    """Adapt the engine's loss provider, fixing unlabeled targets only."""
    def __init__(self, indices, targets):
        self.indices = indices.clone()
        self.targets = targets.clone()

    def gradient(self, r, y):
        assigned = y.clone()
        assigned[self.indices] = self.targets
        return super().gradient(r, assigned)

    def evaluate(self, r, y):
        assigned = y.clone()
        assigned[self.indices] = self.targets
        return super().evaluate(r, assigned)


class FrozenSelectionGD(SelfTrainedGradientDescent):
    def selection_mask(self, scores):
        return self.frozen_selection.to(scores)


def terminal_configuration_type(p):
    values = set(np.asarray(p).tolist())
    if values == {-1}: return 'fully negative selected'
    if values == {1}: return 'fully positive selected'
    if values == {0}: return 'all unselected'
    if values == {-1, 0}: return 'negative selected plus zeros'
    if values == {0, 1}: return 'positive selected plus zeros'
    return 'both selected signs' + (' plus zeros' if 0 in values else '')


class TrajectoryRecorder:
    def __init__(self, X, env, cfg, p, start=0, frozen_targets=None, frozen_mask=None):
        self.X, self.env, self.cfg, self.p, self.start = X, env, cfg, p, start
        self.fixed_targets, self.fixed_mask = frozen_targets, frozen_mask
        self.rows, self.steps = [], []
        self.previous = None

    @torch.no_grad()
    def __call__(self, learner, t):
        env, cfg = self.env, self.cfg
        scores = compute_scores(self.X, learner.bias, learner.weights)
        r = scores[env.I_U]
        conf = configuration(r, cfg.kappa_minus, cfg.kappa_plus)
        pred = sign_with_positive_tie(r)
        y = env.Y[env.I_U]
        tau = float(torch.linalg.vector_norm(learner.weights) / env.d**.5)
        m, b = float(env.mu @ learner.weights / env.d), float(learner.bias)
        row = dict(iteration=self.start+t, error=population_error(b,m,tau,cfg.sigma,self.p),
                   b=b,m=m,tau=tau, normalized_bias=b/tau if tau else np.nan,
                   normalized_alignment=m/tau if tau else np.nan,
                   configuration_fractions=[float((conf==c).double().mean()) for c in (-1,0,1)],
                   prediction_fractions=[float((pred==c).double().mean()) for c in (-1,1)],
                   selected_false_negative_fraction=float(((conf==-1)&(y==1)).double().mean()),
                   selected_false_positive_fraction=float(((conf==1)&(y==-1)).double().mean()))
        selected = conf != 0
        # Score-induced configurations may change during a frozen intervention.
        # Keep the actual objective assignments distinguishable in saved output.
        fit_conf = conf if self.fixed_targets is None else (self.fixed_mask*self.fixed_targets).long()
        if self.fixed_targets is None and self.start+t == 0:
            fit_conf = (selected*learner.initialization_.Y_init[env.I_U]).long()
        row['fitted_configuration_fractions'] = [float((fit_conf==c).double().mean()) for c in (-1,0,1)]
        row['assigned_selected_false_negative_fraction'] = float(((fit_conf==-1)&(y==1)).double().mean())
        row['assigned_selected_false_positive_fraction'] = float(((fit_conf==1)&(y==-1)).double().mean())
        # Both pool-normalized counts and conditional error rates are explicit.
        for name, mask in [('false_negative',conf==-1),('false_positive',conf==1)]:
            errors = mask & (pred != y)
            row['selected_'+name+'_rate'] = float(errors.sum()/mask.sum()) if mask.any() else np.nan
        row['selected_error_rate'] = float((selected & (pred!=y)).sum()/selected.sum()) if selected.any() else np.nan
        if self.previous is not None:
            old_scores, old_conf, old_b, old_w = self.previous
            record = learner.update_records_[-1]
            old_r = old_scores[env.I_U]
            targets = record.pseudo_labels[env.I_U] if self.fixed_targets is None else self.fixed_targets
            mask = record.selection[env.I_U]
            lab_r, lab_y = old_scores[env.I_L], env.Y[env.I_L]
            z_l = cfg.eta * torch.mean(lab_y * torch.sigmoid(-lab_y*lab_r))
            z_u = cfg.eta * torch.mean(mask * targets * torch.sigmoid(-targets*old_r))
            correct = cfg.eta * torch.mean(mask * y * torch.sigmoid(-y*old_r))
            beta_actual = torch.mean(mask*y*(targets != y))
            self_targets = sign_with_positive_tie(old_r)
            beta = torch.mean(mask*y*(self_targets != y))
            db = b-old_b
            feature = (self.X @ (learner.weights-old_w))[env.I_U] / env.d**.5
            dr = r-old_r
            transitions = torch.bincount(((old_conf+1)*3+conf+1).long(),minlength=9).reshape(3,3)
            step = dict(iteration=self.start+t-1, zeta_L=float(z_l),zeta_U=float(z_u),
                        delta_b=db,beta=float(beta),beta_assigned=float(beta_actual),
                        correctly_labeled_selected_zeta_U=float(correct),
                        oracle_identity_residual=float(cfg.pi*(z_u-correct)+cfg.eta*cfg.pi*beta_actual),
                        bias_update_residual=db-float(z_l+cfg.pi*z_u),
                        score_update_residual=float(torch.max(torch.abs(dr-db-feature))),
                        dynamic_self_label_zeta_U=float(cfg.eta*torch.mean(mask*self_targets*torch.sigmoid(-old_r.abs())))
                        if self.fixed_targets is None and self.start+t-1>=1 else np.nan,
                        transition_counts=transitions.numpy(), switches=int((old_conf!=conf).sum()))
            crossings = {}
            masks = {'minus_up':(old_r<=cfg.kappa_minus)&(r>cfg.kappa_minus),
                     'minus_down':(old_r>cfg.kappa_minus)&(r<=cfg.kappa_minus),
                     'plus_up':(old_r<cfg.kappa_plus)&(r>=cfg.kappa_plus),
                     'plus_down':(old_r>=cfg.kappa_plus)&(r<cfg.kappa_plus)}
            for name, crossing in masks.items():
                count = int(crossing.sum())
                crossings[name] = dict(count=count,mean_bias=db if count else np.nan,
                    mean_feature=float(feature[crossing].mean()) if count else np.nan,
                    mean_total=float(dr[crossing].mean()) if count else np.nan,
                    mean_abs_bias=abs(db) if count else np.nan,
                    mean_abs_feature=float(feature[crossing].abs().mean()) if count else np.nan)
            step['crossings'] = crossings
            self.steps.append(step)
        self.rows.append(row)
        self.previous = (scores, conf, b, learner.weights.clone())

    def result(self, learner):
        states = {key:np.asarray([r[key] for r in self.rows]) for key in self.rows[0]}
        keys = ['iteration','zeta_L','zeta_U','delta_b','beta','beta_assigned',
                'correctly_labeled_selected_zeta_U','oracle_identity_residual','bias_update_residual',
                'score_update_residual','dynamic_self_label_zeta_U','transition_counts','switches']
        updates = {key:np.asarray([r[key] for r in self.steps]) for key in keys}
        if not self.steps: updates['transition_counts'] = np.empty((0,3,3),dtype=int)
        updates['crossings'] = {name:{key:np.asarray([r['crossings'][name][key] for r in self.steps])
            for key in ['count','mean_bias','mean_feature','mean_total','mean_abs_bias','mean_abs_feature']}
            for name in ['minus_up','minus_down','plus_up','plus_down']}
        fullneg = states['iteration'][states['configuration_fractions'][:,0]==1]
        switched = updates['iteration'][updates['switches']>0]+1
        return dict(states=states,updates=updates,summary=dict(
            first_fully_negative_selected_iteration=int(fullneg[0]) if len(fullneg) else None,
            last_observed_switch=int(switched[-1]) if len(switched) else None,
            total_configuration_switches=int(updates['switches'].sum()),
            terminal_configuration_type=terminal_configuration_type(self.previous[1].numpy())),
            endpoint=dict(b=float(learner.bias),w=learner.weights.numpy().copy(),configuration=self.previous[1].numpy().astype(np.int8)))


def fit_trajectory(dataset, cfg, initialization=None, start=0, p0=None, oracle=False):
    """Run baseline/replay/frozen interventions through the original fit_full."""
    env, X = dataset.environment, dataset.X
    initialization = dataset.initialization if initialization is None else initialization
    algo = cfg.algorithm_config(T=cfg.T-start)
    targets = mask = None
    if p0 is not None:
        p0 = torch.as_tensor(p0)
        if p0.shape != (env.M,) or not torch.all((p0==-1)|(p0==0)|(p0==1)):
            raise ValueError('p0 must be an M-vector in {-1,0,+1}')
        mask = (p0!=0).double()
        targets = env.Y[env.I_U].clone() if oracle else torch.where(p0==0,1,p0).double()
        algo = replace(algo,loss_function=FrozenTargets(env.I_U,targets))
        learner = FrozenSelectionGD(algo)
        learner.frozen_selection = torch.zeros(env.n)
        learner.frozen_selection[env.I_U] = mask
    else:
        learner = SelfTrainedGradientDescent(algo)
    recorder = TrajectoryRecorder(X,env,cfg,dataset.p,start,targets,mask)
    learner.callback = recorder
    learner.fit_full(X,env,initialization)
    return recorder.result(learner), learner


def checkpoint_initialization(dataset,b,w):
    """At t0>=1 the replay's local t=0 must use the current score signs."""
    scores = compute_scores(dataset.X,b,w)
    return SelfTrainingInitialization.from_unlabeled_labels(dataset.environment,
        b_init=b,w_init=w,Y_init_unlabeled=sign_with_positive_tie(scores[dataset.environment.I_U]))


def run_checkpoint_experiment(dataset,cfg,seed):
    from .optimization import minimize_frozen, branch_consistency
    baseline, learner = fit_trajectory(dataset,cfg)
    errors = baseline['states']['error']
    t_best = 1+int(np.argmin(errors[1:]))
    checkpoints = sorted({max(1,t_best//2),t_best})
    result = dict(seed=seed,p=dataset.p,data_metadata=dataset.metadata,baseline=baseline,t_best=t_best,
                  checkpoints=[],summary=dict(terminal_error=float(errors[-1]),best_error=float(errors[t_best]),
                  deterioration=float(errors[-1]-errors[t_best]),
                  maximum_post_best_deterioration=float(np.max(errors[t_best:])-errors[t_best]),
                  deteriorated=bool(np.max(errors[t_best:])-errors[t_best]>cfg.deterioration_tolerance)))
    env = dataset.environment
    for t0 in checkpoints:
        w = learner.weight_history_[t0]
        b = learner.update_records_[t0].bias if t0 < cfg.T else learner.bias
        init = checkpoint_initialization(dataset,b,w)
        p0 = configuration(compute_scores(dataset.X,b,w)[env.I_U],cfg.kappa_minus,cfg.kappa_plus)
        point = dict(t0=t0,p0=p0.numpy(),state=dict(b=float(b),w=w.numpy().copy()),continuations={},minimizers={})
        for name in ['dynamic','frozen','oracle']:
            traj, replay = fit_trajectory(dataset,cfg,init,t0,p0 if name!='dynamic' else None,name=='oracle')
            point['continuations'][name] = traj
            if name=='dynamic':
                deviations = [float(torch.max(torch.abs(a-c))) for a,c in zip(replay.weight_history_,learner.weight_history_[t0:])]
                deviations.append(float(np.max(np.abs(traj['states']['b']-baseline['states']['b'][t0:]))))
                point['replay_max_abs'] = max(deviations)
                if point['replay_max_abs'] > cfg.replay_tolerance:
                    raise RuntimeError(f'checkpoint replay failed: {point["replay_max_abs"]}')
            del replay
        for name in ['frozen','oracle']:
            opt = minimize_frozen(dataset.X,env,p0,float(b),w,cfg,oracle=name=='oracle')
            ow = torch.as_tensor(opt['w'])
            tau = float(torch.linalg.vector_norm(ow)/env.d**.5)
            opt['error'] = population_error(opt['b'],float(env.mu@ow/env.d),tau,cfg.sigma,dataset.p)
            opt['consistency'] = branch_consistency(compute_scores(dataset.X,opt['b'],ow)[env.I_U].numpy(),
                p0.numpy(),cfg.kappa_minus,cfg.kappa_plus,solver_converged=opt['converged'],tolerance=cfg.consistency_tolerance)
            opt['consistency']['interpretation'] = 'original pseudo-label branch' if name=='frozen' else 'comparison to original branch only; oracle need not be an equilibrium'
            point['minimizers'][name] = opt
        result['checkpoints'].append(point)
    return result
