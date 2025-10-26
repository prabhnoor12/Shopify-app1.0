from __future__ import annotations
import numpy as np
from scipy import stats
import math
from sqlalchemy.orm import Session
from ..models.ab_test import ABTest
from ..models.variant import Variant


class StatisticalService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def calculate_confidence_interval(successes, trials, confidence_level=0.95):
        """
        Calculates the confidence interval for a proportion using the Wilson score interval.
        Handles zero trials gracefully.
        """
        if trials == 0:
            return 0.0, 0.0

        z = stats.norm.ppf(1 - (1 - confidence_level) / 2)
        p_hat = successes / trials

        denominator = 1 + z**2 / trials
        numerator_term = p_hat + z**2 / (2 * trials)
        interval_term = z * math.sqrt(
            (p_hat * (1 - p_hat) / trials) + (z**2 / (4 * trials**2))
        )

        lower_bound = max(0, (numerator_term - interval_term) / denominator)
        upper_bound = min(1, (numerator_term + interval_term) / denominator)

        return lower_bound, upper_bound

    @staticmethod
    def calculate_proportions_z_test(c1, n1, c2, n2):
        """
        Performs a two-proportion z-test.
        Returns p-value.
        """
        if n1 == 0 or n2 == 0:
            return 1.0

        p1 = c1 / n1
        p2 = c2 / n2

        if n1 + n2 == 0:
            return 1.0

        p_pooled = (c1 + c2) / (n1 + n2)

        if p_pooled <= 0 or p_pooled >= 1:
            return 1.0

        se = math.sqrt(p_pooled * (1 - p_pooled) * (1 / n1 + 1 / n2))
        if se == 0:
            return 1.0

        z_score = (p1 - p2) / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

        return p_value

    @staticmethod
    def calculate_chi_square_test(conversions, impressions):
        """
        Performs a chi-square test for independence on a contingency table.
        `conversions` and `impressions` are lists for all variants.
        Returns p-value.
        """
        if len(conversions) < 2 or len(impressions) < 2 or sum(impressions) == 0:
            return 1.0

        successes = np.array(conversions)
        failures = np.array(impressions) - successes

        if np.any(failures < 0):
            raise ValueError(
                "Impressions must be greater than or equal to conversions."
            )

        contingency_table = np.array([successes, failures])

        try:
            chi2, p, _, _ = stats.chi2_contingency(contingency_table, correction=False)
            return p
        except ValueError:
            return 1.0

    @staticmethod
    def calculate_effect_size_cohen_h(c1, n1, c2, n2, epsilon=1e-6):
        """
        Calculates Cohen's h for effect size between two proportions.
        An epsilon is added to avoid domain errors with proportions of 0 or 1.
        """
        if n1 == 0 or n2 == 0:
            return 0.0

        p1 = max(epsilon, min(1 - epsilon, c1 / n1))
        p2 = max(epsilon, min(1 - epsilon, c2 / n2))

        h = 2 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))
        return h

    @staticmethod
    def bayesian_probability_b_beats_a(c_a, n_a, c_b, n_b, alpha_prior=1, beta_prior=1):
        """
        Calculates the Bayesian probability that variant B is better than variant A.
        Uses a Beta distribution as a prior for the conversion rates.
        """
        alpha_a, beta_a = alpha_prior + c_a, beta_prior + n_a - c_a
        alpha_b, beta_b = alpha_prior + c_b, beta_prior + n_b - c_b

        # Sample from the posterior distributions
        samples_a = np.random.beta(alpha_a, beta_a, size=10000)
        samples_b = np.random.beta(alpha_b, beta_b, size=10000)

        return np.mean(samples_b > samples_a)

    def calculate_t_test(data_a, data_b):
        """
        Performs an independent two-sample t-test.
        `data_a` and `data_b` are lists of continuous metric values.
        Returns p-value.
        """
        if not data_a or not data_b:
            return 1.0

        _, p_value = stats.ttest_ind(data_a, data_b, equal_var=False)  # Welch's t-test
        return p_value

    @staticmethod
    def calculate_power(n, p1, p2, alpha=0.05):
        """
        Performs a power analysis for a two-proportion z-test.
        """
        effect_size = np.abs(p1 - p2)
        power = stats.power.TTestIndPower().power(
            effect_size=effect_size,
            nobs=n,
            alpha=alpha,
            ratio=1.0,
            alternative="two-sided",
        )
        return power

    @staticmethod
    def sequential_probability_ratio_test(
        c1, n1, c2, n2, alpha=0.05, beta=0.2, min_effect=0.01
    ):
        """
        Performs a Sequential Probability Ratio Test (SPRT).
        Returns 'accept_h1', 'accept_h0', or 'continue'.
        """
        if n1 == 0 or n2 == 0:
            return "continue"

        p1 = c1 / n1
        p2 = c2 / n2

        p0 = p1
        p1_h1 = p1 + min_effect

        # Boundaries
        upper_bound = np.log((1 - beta) / alpha)
        lower_bound = np.log(beta / (1 - alpha))

        # Log-likelihood ratio
        llr = (c2 * np.log(p1_h1 / p0)) + ((n2 - c2) * np.log((1 - p1_h1) / (1 - p0)))

        if llr > upper_bound:
            return "accept_h1"  # Significant result
        elif llr < lower_bound:
            return "accept_h0"  # No significant difference
        else:
            return "continue"

    def get_statistically_significant_winner(
        self, test_id: int, alpha: float = 0.05, min_conversions: int = 5
    ) -> Variant | None:
        """
        Determines the winning variant for an A/B test based on statistical significance
        with Bonferroni correction for multiple comparisons.
        """
        ab_test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not ab_test or len(ab_test.variants) < 2:
            return None

        variants = [v for v in ab_test.variants if v.conversions >= min_conversions]
        if len(variants) < 2:
            return None

        variants.sort(
            key=lambda v: (v.conversions / v.impressions) if v.impressions > 0 else 0,
            reverse=True,
        )

        candidate_winner = variants[0]

        # Bonferroni correction
        num_comparisons = len(variants) - 1
        corrected_alpha = alpha / num_comparisons

        is_significant_winner = True
        for other_variant in variants[1:]:
            p_value = self.calculate_proportions_z_test(
                candidate_winner.conversions,
                candidate_winner.impressions,
                other_variant.conversions,
                other_variant.impressions,
            )
            if p_value >= corrected_alpha:
                is_significant_winner = False
                break

        if is_significant_winner:
            return candidate_winner

        return None
