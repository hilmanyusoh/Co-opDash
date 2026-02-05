import pandas as pd
import numpy as np

class CreditScoreCalculator:
    """
    คลาสสำหรับคำนวณคะแนนเครดิตและระดับเครดิตตามมาตรฐาน NCB
    """
    def __init__(self):
        self.weights = {
            'payment_history': 0.35,
            'credit_utilization': 0.30,
            'credit_history_length': 0.15,
            'credit_mix': 0.10,
            'new_credit': 0.10
        }
        self.max_points = {
            'payment_history': 350,
            'credit_utilization': 300,
            'credit_history_length': 150,
            'credit_mix': 100,
            'new_credit': 100
        }

    def calculate_payment_history_score(self, data):
        score = self.max_points['payment_history']
        installments_overdue = data.get('installments_overdue', 0)
        if installments_overdue > 0:
            score -= min(installments_overdue * 30, 150)
        
        payment_perf = data.get('payment_performance_pct', 100)
        if payment_perf < 100:
            score -= (100 - payment_perf) * 1.0
            
        late_12m = data.get('late_payment_count_12m', 0)
        if late_12m > 0:
            score -= min(late_12m * 10, 50)
            
        late_24m = data.get('late_payment_count_24m', 0)
        if late_24m > late_12m:
            score -= min((late_24m - late_12m) * 5, 30)
            
        if data.get('account_status') == 'ผิดนัด':
            score -= 20
        return max(0, score)

    def calculate_credit_utilization_score(self, data):
        score = self.max_points['credit_utilization']
        util_rate = data.get('credit_utilization_rate', 0)
        if util_rate <= 10: penalty = 0
        elif util_rate <= 30: penalty = 50
        elif util_rate <= 50: penalty = 100
        elif util_rate <= 70: penalty = 150
        elif util_rate <= 90: penalty = 200
        elif util_rate <= 100: penalty = 250
        else: penalty = 300
        return max(0, score - penalty)

    def calculate_credit_history_length_score(self, data):
        oldest_months = data.get('oldest_account_months', 0)
        if oldest_months < 6: score = 0
        elif oldest_months <= 12: score = 30
        elif oldest_months <= 24: score = 60
        elif oldest_months <= 36: score = 90
        elif oldest_months <= 48: score = 120
        elif oldest_months <= 60: score = 135
        else:
            years_over_5 = (oldest_months - 60) / 12
            score = 135 + min(years_over_5 * 2.5, 15)
        return min(score, self.max_points['credit_history_length'])

    def calculate_credit_mix_score(self, data):
        total_accounts = data.get('total_accounts', 0)
        active_accounts = data.get('active_accounts', 0)
        if total_accounts == 0: score = 0
        elif total_accounts <= 1: score = 20
        elif total_accounts <= 3: score = 50
        elif total_accounts <= 5: score = 75
        elif total_accounts <= 7: score = 90
        else: score = 100
        bonus = min(active_accounts * 5, 20)
        return min(score + bonus, self.max_points['credit_mix'])

    def calculate_new_credit_score(self, data):
        score = self.max_points['new_credit']
        inq_6m = data.get('inquiries_6m', 0)
        inq_12m = data.get('inquiries_12m', 0)
        penalty = (min(inq_6m * 10, 50)) + (min((inq_12m - inq_6m) * 5, 50))
        return max(0, score - penalty)

    def get_credit_rating(self, score):
        if score >= 753: return 'AA'
        if score >= 725: return 'BB'
        if score >= 699: return 'CC'
        if score >= 681: return 'DD*'
        if score >= 666: return 'EE'
        if score >= 646: return 'FF'
        if score >= 616: return 'GG'
        return 'HH'

    def calculate_all(self, data):
        """รวมผลการคำนวณทั้งหมด"""
        p = self.calculate_payment_history_score(data)
        u = self.calculate_credit_utilization_score(data)
        h = self.calculate_credit_history_length_score(data)
        m = self.calculate_credit_mix_score(data)
        n = self.calculate_new_credit_score(data)
        
        total = max(300, min(900, p + u + h + m + n))
        rating = self.get_credit_rating(total)
        
        return {
            'credit_score': int(total),
            'credit_rating': rating,
            'breakdown': {'p': p, 'u': u, 'h': h, 'm': m, 'n': n}
        }