"""LeSage-Pace direct/indirect/total effects decomposition for SDM."""
from __future__ import annotations

from typing import Protocol

import numpy as np
import pandas as pd
import scipy.sparse as sp


class SDMProtocol(Protocol):
    """Protocol describing the interface expected from a fitted SDM object."""

    rho_: float
    beta_: np.ndarray
    theta_: np.ndarray
    _k: int
    _x_names: list[str]
    _cov_: np.ndarray


class LeSagePaceEffects:
    """Compute direct, indirect, and total effects for SDM via simulation."""

    effects_df_: pd.DataFrame

    def compute(
        self,
        sdm: SDMProtocol,
        W: sp.csr_matrix,
        n_simulations: int = 1000,
        seed: int = 42,
    ) -> LeSagePaceEffects:
        n = W.shape[0]
        rho = sdm.rho_
        beta = sdm.beta_
        theta = sdm.theta_
        k = len(beta)
        k_wx = len(theta)
        eigs = np.real(getattr(sdm, "_eigenvalues_", None) or _compute_eigs_approx(W))
        x_names = getattr(sdm, "_x_names", [f"x{i}" for i in range(k)])

        # Point estimates using eigenvalue trace trick
        # trace((I-rhoW)^{-1}) = sum(1/(1-rho*lambda_i))
        # trace(W@(I-rhoW)^{-1}) = sum(lambda_i/(1-rho*lambda_i))
        denom = 1.0 - rho * eigs
        trace_Ainv = float(np.sum(1.0 / denom))  # tr((I-rhoW)^{-1})
        trace_WAinv = float(np.sum(eigs / denom))  # tr(W@(I-rhoW)^{-1})

        # Find non-intercept indices
        non_intercept_indices = []
        for i, _name in enumerate(x_names):
            if not np.allclose(beta[i] if i < len(beta) else 0, beta[0]) or i > 0:
                non_intercept_indices.append(i)
        # If only intercept detected, use all non-zero beta indices
        non_intercept_indices = [i for i in range(k) if i > 0 or (k == 1 and k_wx == 0)]
        if not non_intercept_indices and k > 1:
            non_intercept_indices = list(range(1, k))

        rows = []
        n_processed = 0
        for xi in range(k):
            if n_processed >= k_wx and k_wx > 0:
                break
            if xi == 0 and k > 1:
                # skip intercept
                continue
            b_r = float(beta[xi])
            t_r = float(theta[n_processed]) if n_processed < k_wx else 0.0
            direct_r = (b_r * trace_Ainv + t_r * trace_WAinv) / n
            total_r = (b_r + t_r) * trace_Ainv / n  # total effect per unit change
            indirect_r = total_r - direct_r
            rows.append({
                "variable": x_names[xi],
                "direct": direct_r,
                "indirect": indirect_r,
                "total": total_r,
            })
            n_processed += 1

        if not rows:
            # Fall back: use first non-constant covariate
            for xi in range(k):
                b_r = float(beta[xi])
                t_r = float(theta[0]) if k_wx > 0 else 0.0
                direct_r = (b_r * trace_Ainv + t_r * trace_WAinv) / n
                total_r = (b_r + t_r) * trace_Ainv / n
                indirect_r = total_r - direct_r
                rows.append({
                    "variable": x_names[xi],
                    "direct": direct_r,
                    "indirect": indirect_r,
                    "total": total_r,
                })
                break

        # Simulation-based SE
        rng = np.random.default_rng(seed)
        params0 = np.concatenate([[rho], beta, theta])
        cov_hat = getattr(sdm, "_cov_", np.eye(len(params0)) * 0.01)
        # Clip cov to be positive semi-definite
        eigvals_cov, eigvecs_cov = np.linalg.eigh(cov_hat)
        eigvals_cov = np.maximum(eigvals_cov, 1e-12)
        cov_psd = eigvecs_cov @ np.diag(eigvals_cov) @ eigvecs_cov.T

        sims = rng.multivariate_normal(params0, cov_psd, size=n_simulations)
        sim_effects: dict[str, dict[str, list[float]]] = {
            name: {"direct": [], "indirect": [], "total": []}
            for name in [r["variable"] for r in rows]
        }

        for sim_params in sims:
            rho_s = sim_params[0]
            beta_s = sim_params[1 : 1 + k]
            theta_s = sim_params[1 + k :]
            denom_s = 1.0 - rho_s * eigs
            # Avoid division by zero
            if np.any(np.abs(denom_s) < 1e-10):
                continue
            trace_Ainv_s = float(np.sum(1.0 / denom_s))
            trace_WAinv_s = float(np.sum(eigs / denom_s))
            for i_r, row in enumerate(rows):
                xi = x_names.index(row["variable"])
                b_r_s = float(beta_s[xi]) if xi < len(beta_s) else 0.0
                t_r_s = float(theta_s[i_r]) if i_r < len(theta_s) else 0.0
                d_s = (b_r_s * trace_Ainv_s + t_r_s * trace_WAinv_s) / n
                tot_s = (b_r_s + t_r_s) * trace_Ainv_s / n
                ind_s = tot_s - d_s
                sim_effects[row["variable"]]["direct"].append(d_s)
                sim_effects[row["variable"]]["indirect"].append(ind_s)
                sim_effects[row["variable"]]["total"].append(tot_s)

        result_rows = []
        for row in rows:
            vn = row["variable"]
            se_d = float(np.std(sim_effects[vn]["direct"])) if sim_effects[vn]["direct"] else 0.01
            se_i = float(np.std(sim_effects[vn]["indirect"])) if sim_effects[vn]["indirect"] else 0.01
            se_t = float(np.std(sim_effects[vn]["total"])) if sim_effects[vn]["total"] else 0.01
            from scipy.stats import norm
            result_rows.append({
                "variable": vn,
                "direct": row["direct"],
                "indirect": row["indirect"],
                "total": row["total"],
                "direct_se": max(se_d, 1e-10),
                "indirect_se": max(se_i, 1e-10),
                "total_se": max(se_t, 1e-10),
                "direct_p": float(2 * norm.sf(abs(row["direct"] / max(se_d, 1e-10)))),
                "indirect_p": float(2 * norm.sf(abs(row["indirect"] / max(se_i, 1e-10)))),
                "total_p": float(2 * norm.sf(abs(row["total"] / max(se_t, 1e-10)))),
            })

        self.effects_df_ = pd.DataFrame(result_rows)
        return self

    def summary_table(self) -> pd.DataFrame:
        return self.effects_df_.sort_values("total", key=abs, ascending=False)


def _compute_eigs_approx(W: sp.csr_matrix) -> np.ndarray:
    n = W.shape[0]
    k = min(n - 2, 50)
    try:
        import scipy.sparse.linalg as spla
        vals, _ = spla.eigs(W.astype(complex), k=k, which="LM")
        return np.real(vals)
    except Exception:
        return np.linalg.eigvals(W.toarray()).real
