from users.models import Achievement, UserAchievement
from .models import ReadingChallenge, DailyReadingLog
from django.utils import timezone
import math

def calculate_xp_for_reading(pages=0, chapters=0):
    """
    Simple XP formula:
    - 2 XP per page read
    - 10 XP per chapter read
    """
    return (pages * 2) + (chapters * 10)

def get_level_threshold(level):
    """
    XP required to reach the NEXT level.
    Scale: 100 * (level ^ 1.5)
    L1 -> L2: 100
    L2 -> L3: 282
    L3 -> L4: 519
    """
    import math
    return int(100 * math.pow(level, 1.5))

def add_xp_to_user(user, xp_amount):
    """
    Adds XP and handles leveling up.
    Returns (leveled_up, new_level)
    """
    user.xp += xp_amount
    leveled_up = False
    
    while user.xp >= get_level_threshold(user.level):
        user.xp -= get_level_threshold(user.level)
        user.level += 1
        leveled_up = True
        
    user.save()
    return leveled_up, user.level

def award_achievement(user, achievement_code):
    """
    Awards an achievement to a user if they don't have it yet.
    Returns (awarded, achievement_obj)
    """
    try:
        achievement = Achievement.objects.get(code=achievement_code)
        obj, created = UserAchievement.objects.get_or_create(
            user=user,
            achievement=achievement
        )
        if created:
            # Also give XP reward
            add_xp_to_user(user, achievement.xp_reward)
            return True, achievement
    except Achievement.DoesNotExist:
        pass
    return False, None

def check_reading_achievements(user, log_entry):
    """
    Checks for reading-related achievements after a new log entry.
    """
    new_achievements = []
    
    # 1. First Book Achievement
    # Check if the challenge is now completed
    if log_entry.challenge.is_completed:
        awarded, ach = award_achievement(user, 'first_book')
        if awarded: new_achievements.append(ach)

    # 2. Night Owl Achievement
    # If logged after 11 PM (23:00)
    if timezone.now().hour >= 23 or timezone.now().hour <= 4:
        awarded, ach = award_achievement(user, 'night_owl')
        if awarded: new_achievements.append(ach)
        
    # 3. Streak 7 Achievement
    # We could calculate current streak here or use a simplified version
    # For now, let's keep it simple.
    
    return new_achievements
