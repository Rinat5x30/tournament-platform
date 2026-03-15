# admin_panel/forms.py - ИСПРАВЛЕННАЯ ВЕРСИЯ

from django import forms
from django.utils.text import slugify
from tournaments.models import Tournament, Season, Stage, TournamentTeam, TableZone
from matches.models import Match, MatchStatistics, Goal, PlayerMatchStats
from teams.models import Team, TeamMember
from accounts.models import User

class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = [
            'name', 'slug', 'season', 'description', 'logo',
            'status', 'stage_type', 'start_date', 'end_date',
            'registration_start', 'registration_end',
            'max_teams', 'stream_url'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название турнира'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Оставьте пустым для автоматической генерации'
            }),
            'season': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'stage_type': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'registration_start': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'registration_end': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'max_teams': forms.NumberInput(attrs={'class': 'form-control'}),
            'stream_url': forms.URLInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False
        self.fields['start_date'].input_formats = ['%Y-%m-%d']
        self.fields['end_date'].input_formats = ['%Y-%m-%d']
        self.fields['registration_start'].input_formats = ['%Y-%m-%d']
        self.fields['registration_end'].input_formats = ['%Y-%m-%d']
    
    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        name = self.cleaned_data.get('name')
        
        if not slug and name:
            slug = slugify(name)
            counter = 1
            original_slug = slug
            while Tournament.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
        
        return slug


# ИСПРАВЛЕНО: Добавлено поле is_active
class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'tag', 'slug', 'logo', 'captain', 'founded_date', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название команды'
            }),
            'tag': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'FC, TM, UNI...',
                'maxlength': '5'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Оставьте пустым для автоматической генерации'
            }),
            'captain': forms.Select(attrs={'class': 'form-control'}),
            'founded_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False
        
        # ИСПРАВЛЕНО: Исключаем капитанов других команд
        # Показываем только игроков без команды или текущего капитана (при редактировании)
        existing_captains = Team.objects.exclude(
            pk=self.instance.pk if self.instance.pk else None
        ).filter(captain__isnull=False).values_list('captain_id', flat=True)
        
        self.fields['captain'].queryset = User.objects.filter(
            role__in=['player', 'captain']
        ).exclude(id__in=existing_captains)
        
        self.fields['captain'].required = False
        self.fields['founded_date'].input_formats = ['%Y-%m-%d']
        self.fields['founded_date'].required = False
        self.fields['tag'].required = False
        self.fields['description'].required = False
        self.fields['is_active'].required = False
        
        # КРИТИЧЕСКИ ВАЖНО: Устанавливаем значение по умолчанию для новых команд
        if not self.instance.pk:
            self.initial['is_active'] = True
    
    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        name = self.cleaned_data.get('name')
        
        if not slug and name:
            slug = slugify(name)
            counter = 1
            original_slug = slug
            while Team.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
        
        return slug


class StageForm(forms.ModelForm):
    class Meta:
        model = Stage
        fields = [
            'name', 'order', 'stage_type',
            'swiss_rounds', 'groups_count', 'teams_per_group',
            'tiebreaker_1', 'tiebreaker_2', 'tiebreaker_3'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'stage_type': forms.Select(attrs={'class': 'form-control'}),
            'swiss_rounds': forms.NumberInput(attrs={'class': 'form-control'}),
            'groups_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'teams_per_group': forms.NumberInput(attrs={'class': 'form-control'}),
            'tiebreaker_1': forms.Select(attrs={'class': 'form-control'}),
            'tiebreaker_2': forms.Select(attrs={'class': 'form-control'}),
            'tiebreaker_3': forms.Select(attrs={'class': 'form-control'}),
        }

class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = [
            'tournament', 'stage', 'round_number',
            'team1', 'team2', 'scheduled_time',
            'status', 'stream_url', 'protocol', 'notes'
        ]
        widgets = {
            'tournament': forms.Select(attrs={'class': 'form-control'}),
            'stage': forms.Select(attrs={'class': 'form-control'}),
            'round_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'team1': forms.Select(attrs={'class': 'form-control'}),
            'team2': forms.Select(attrs={'class': 'form-control'}),
            'scheduled_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'stream_url': forms.URLInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MatchResultForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = [
            'score_team1', 'score_team2',
            'actual_start_time', 'actual_end_time',
            'protocol', 'notes'
        ]
        widgets = {
            'score_team1': forms.NumberInput(attrs={'class': 'form-control'}),
            'score_team2': forms.NumberInput(attrs={'class': 'form-control'}),
            'actual_start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'actual_end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TournamentTeamForm(forms.ModelForm):
    class Meta:
        model = TournamentTeam
        fields = ['team', 'seed']
        widgets = {
            'team': forms.Select(attrs={'class': 'form-control'}),
            'seed': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class TableZoneForm(forms.ModelForm):
    class Meta:
        model = TableZone
        fields = ['name', 'zone_type', 'start_position', 'end_position', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'zone_type': forms.Select(attrs={'class': 'form-control'}),
            'start_position': forms.NumberInput(attrs={'class': 'form-control'}),
            'end_position': forms.NumberInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }

class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ['player', 'role', 'jersey_number', 'joined_date', 'left_date', 'is_active']
        widgets = {
            'player': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'jersey_number': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '99'}),
            'joined_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }, format='%Y-%m-%d'),
            'left_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }, format='%Y-%m-%d'),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['player'].queryset = User.objects.filter(
            role__in=['player', 'captain']
        ).order_by('username')
        self.fields['left_date'].required = False
        self.fields['jersey_number'].required = False
        self.fields['joined_date'].input_formats = ['%Y-%m-%d']
        self.fields['left_date'].input_formats = ['%Y-%m-%d']
    
    def clean(self):
        cleaned_data = super().clean()
        player = cleaned_data.get('player')
        joined_date = cleaned_data.get('joined_date')
        left_date = cleaned_data.get('left_date')
        
        if joined_date and left_date and left_date < joined_date:
            raise forms.ValidationError('Дата выхода не может быть раньше даты вступления')
        
        return cleaned_data