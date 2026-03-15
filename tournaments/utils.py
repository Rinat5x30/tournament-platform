# tournaments/utils.py

from datetime import datetime, timedelta
from typing import List, Tuple
import random
from matches.models import Match


class SwissSystemGenerator:
    """Генератор пар для швейцарской системы"""
    
    def __init__(self, stage, teams):
        self.stage = stage
        self.teams = list(teams)
        self.rounds = stage.swiss_rounds or self._calculate_rounds()
    
    def _calculate_rounds(self):
        """Автоматический расчет количества раундов"""
        import math
        return math.ceil(math.log2(len(self.teams)))
    
    def generate_pairings(self, round_number: int) -> List[Tuple]:
        """Генерация пар для раунда"""
        if round_number == 1:
            return self._first_round_pairings()
        else:
            return self._subsequent_round_pairings(round_number)
    
    def _first_round_pairings(self):
        """Первый раунд - случайные пары или по сиду"""
        teams = self.teams.copy()
        
        # Сортируем по сиду если есть
        teams.sort(key=lambda t: getattr(t, 'seed', 999))
        
        # Если ускоренная система - топ играет с топом
        if self.stage.use_accelerated_pairing:
            mid = len(teams) // 2
            top_half = teams[:mid]
            bottom_half = teams[mid:]
            return list(zip(top_half, bottom_half))
        
        # Обычная система - 1 vs 2, 3 vs 4, etc
        pairs = []
        for i in range(0, len(teams), 2):
            if i + 1 < len(teams):
                pairs.append((teams[i], teams[i + 1]))
        return pairs
    
    def _subsequent_round_pairings(self, round_number):
        """Последующие раунды - по очкам"""
        # Получаем текущие очки команд
        standings = self._get_current_standings()
        
        # Группируем по очкам
        score_groups = {}
        for team, score in standings.items():
            if score not in score_groups:
                score_groups[score] = []
            score_groups[score].append(team)
        
        # Генерируем пары внутри групп
        pairs = []
        for score in sorted(score_groups.keys(), reverse=True):
            group = score_groups[score]
            random.shuffle(group)  # Случайное распределение внутри группы
            
            for i in range(0, len(group), 2):
                if i + 1 < len(group):
                    # Проверяем, не играли ли команды раньше
                    if not self._have_played(group[i], group[i + 1]):
                        pairs.append((group[i], group[i + 1]))
                    else:
                        # Ищем альтернативную пару
                        pairs.append((group[i], group[i + 1]))  # Упрощенно
        
        return pairs
    
    def _get_current_standings(self):
        """Получить текущую турнирную таблицу"""
        standings = {}
        matches = Match.objects.filter(
            stage=self.stage,
            status='finished'
        )
        
        for team in self.teams:
            standings[team] = 0
        
        for match in matches:
            if match.score_team1 > match.score_team2:
                standings[match.team1] = standings.get(match.team1, 0) + 3
            elif match.score_team1 < match.score_team2:
                standings[match.team2] = standings.get(match.team2, 0) + 3
            else:
                standings[match.team1] = standings.get(match.team1, 0) + 1
                standings[match.team2] = standings.get(match.team2, 0) + 1
        
        return standings
    
    def _have_played(self, team1, team2):
        """Проверить, играли ли команды между собой"""
        return Match.objects.filter(
            stage=self.stage,
            team1__in=[team1, team2],
            team2__in=[team1, team2]
        ).exclude(
            team1=team2
        ).exists()


class EliminationBracketGenerator:
    """Генератор сетки плей-офф"""
    
    def __init__(self, stage, teams, double_elimination=False):
        self.stage = stage
        self.teams = list(teams)
        self.double_elimination = double_elimination
    
    def generate_bracket(self):
        """Генерация полной сетки"""
        # Определяем количество команд (должно быть степенью 2)
        import math
        rounds_count = math.ceil(math.log2(len(self.teams)))
        bracket_size = 2 ** rounds_count
        
        # Добавляем "пустые" команды если нужно
        while len(self.teams) < bracket_size:
            self.teams.append(None)
        
        # Первый раунд
        first_round = self._generate_first_round()
        
        if self.double_elimination:
            return self._generate_double_elimination(first_round)
        else:
            return self._generate_single_elimination(first_round)
    
    def _generate_first_round(self):
        """Генерация первого раунда по сидам"""
        teams = self.teams.copy()
        teams.sort(key=lambda t: getattr(t, 'seed', 999) if t else 999)
        
        # Классическая схема: 1 vs 16, 8 vs 9, 4 vs 13, и т.д.
        n = len(teams)
        pairs = []
        
        for i in range(n // 2):
            team1 = teams[i]
            team2 = teams[n - 1 - i]
            pairs.append((team1, team2))
        
        return pairs
    
    def _generate_single_elimination(self, first_round):
        """Генерация Single Elimination"""
        matches = []
        round_number = 1
        current_pairs = first_round
        
        while len(current_pairs) > 0:
            round_matches = []
            for team1, team2 in current_pairs:
                if team1 and team2:  # Пропускаем пустые пары
                    match = {
                        'round': round_number,
                        'team1': team1,
                        'team2': team2,
                        'winner_advances_to': len(current_pairs) // 2
                    }
                    round_matches.append(match)
            
            matches.extend(round_matches)
            
            if len(current_pairs) == 1:
                break
            
            # Следующий раунд (пары из победителей)
            current_pairs = [(None, None) for _ in range(len(current_pairs) // 2)]
            round_number += 1
        
        return matches
    
    def _generate_double_elimination(self, first_round):
        """Генерация Double Elimination"""
        # Winners bracket
        winners_bracket = self._generate_single_elimination(first_round)
        
        # Losers bracket (упрощенная версия)
        # В реальной реализации нужно отслеживать проигравших из winners bracket
        
        return {
            'winners': winners_bracket,
            'losers': [],  # TODO: реализовать losers bracket
            'grand_final': None
        }


class ScheduleGenerator:
    """Генератор расписания по слотам"""
    
    def __init__(self, tournament, time_slots):
        self.tournament = tournament
        self.time_slots = list(time_slots)
    
    def schedule_matches(self, matches_list):
        """Распределить матчи по слотам"""
        scheduled = []
        current_date = self.tournament.start_date
        slot_index = 0
        matches_in_slot = 0
        
        for match in matches_list:
            # Находим подходящий слот
            while slot_index < len(self.time_slots):
                slot = self.time_slots[slot_index]
                
                # Проверяем день недели
                while current_date.weekday() != slot.day_of_week:
                    current_date += timedelta(days=1)
                
                # Проверяем, не заполнен ли слот
                if matches_in_slot < slot.max_matches:
                    match_time = datetime.combine(
                        current_date,
                        slot.start_time
                    )
                    scheduled.append((match, match_time))
                    matches_in_slot += 1
                    break
                else:
                    # Переходим к следующему слоту
                    slot_index += 1
                    matches_in_slot = 0
                    if slot_index >= len(self.time_slots):
                        # Начинаем следующий день
                        current_date += timedelta(days=1)
                        slot_index = 0
        
        return scheduled


class TiebreakerResolver:
    """Разрешение ничьих по тайбрейкерам"""
    
    def __init__(self, stage):
        self.stage = stage
    
    def resolve(self, teams_data):
        """Применить тайбрейкеры к командам с одинаковыми очками"""
        tiebreakers = [
            self.stage.tiebreaker_1,
            self.stage.tiebreaker_2,
            self.stage.tiebreaker_3
        ]
        
        # Группируем команды по очкам
        score_groups = {}
        for team_data in teams_data:
            points = team_data['points']
            if points not in score_groups:
                score_groups[points] = []
            score_groups[points].append(team_data)
        
        # Применяем тайбрейкеры к каждой группе
        result = []
        for points in sorted(score_groups.keys(), reverse=True):
            group = score_groups[points]
            
            if len(group) > 1:
                # Применяем тайбрейкеры
                for tiebreaker in tiebreakers:
                    group = self._apply_tiebreaker(group, tiebreaker)
                    if len(set(self._get_sort_key(t, tiebreaker) for t in group)) == len(group):
                        break  # Все команды различимы
            
            result.extend(group)
        
        return result
    
    def _apply_tiebreaker(self, teams, tiebreaker_type):
        """Применить конкретный тайбрейкер"""
        if tiebreaker_type == 'goal_difference':
            return sorted(teams, key=lambda t: t['goal_diff'], reverse=True)
        elif tiebreaker_type == 'goals_scored':
            return sorted(teams, key=lambda t: t['goals_for'], reverse=True)
        elif tiebreaker_type == 'goals_conceded':
            return sorted(teams, key=lambda t: t['goals_against'])
        elif tiebreaker_type == 'wins':
            return sorted(teams, key=lambda t: t['wins'], reverse=True)
        elif tiebreaker_type == 'head_to_head':
            return self._head_to_head(teams)
        elif tiebreaker_type == 'random':
            random.shuffle(teams)
            return teams
        
        return teams
    
    def _get_sort_key(self, team_data, tiebreaker_type):
        """Получить ключ сортировки для тайбрейкера"""
        if tiebreaker_type == 'goal_difference':
            return team_data['goal_diff']
        elif tiebreaker_type == 'goals_scored':
            return team_data['goals_for']
        elif tiebreaker_type == 'goals_conceded':
            return -team_data['goals_against']
        elif tiebreaker_type == 'wins':
            return team_data['wins']
        return 0
    
    def _head_to_head(self, teams):
        """Тайбрейкер по личным встречам"""
        # Упрощенная реализация
        # TODO: подсчитать результаты между этими командами
        return teams