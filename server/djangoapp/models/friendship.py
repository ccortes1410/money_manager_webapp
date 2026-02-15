from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Friendship(models.Model):
    """
    Track friend relationships between users.
    The relationship is two-way once accepted.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('blocked', 'Blocked'),
    ]

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_friend_requests'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_friend_requests'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['sender', 'receiver']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.status})"
    
    def accept(self):
        """Accept the friend request."""
        self.status = 'accepted'
        self.save()

    def decline(self):
        """Decline the friend request."""
        self.status = 'declined'
        self.save()

    def block(self):
        self.status = 'blocked'
        self.svae()

    @classmethod
    def are_friends(cls, user1, user2):
        """Check if two users are friends."""
        return cls.objects.filter(
            models.Q(sender=user1, receiver=user2, status='accepted') |
            models.Q(sender=user2, receiver=user1, status='accepted')
        ).exists()

    @classmethod
    def get_friends(cls, user):
        """Get all friends for a user."""
        # Get friendships where user is sender or recevier and status is accepted
        friendships = cls.objects.filter(
            models.Q(sender=user, status='accepted') |
            models.Q(receiver=user, status='accepted')
        )

        friends = []
        for friendship in friendships:
            if friendship.sender == user:
                friends.append(friendship.receiver)
            else:
                friends.append(friendship.sender)
        
        return friends

    @classmethod
    def get_pending_requests(cls, user):
        """Get pening friend requests received by user."""
        return cls.objects.filter(receiver=user, status='pending')
    
    @classmethod
    def get_sent_requests(cls, user):
        """Get pending friend requests sent by user."""
        return cls.objects.filter(sender=user, status='pending')
    
    @classmethod
    def is_blocked(cls, user1, user2):
        """Check if either user has blocked the other."""
        return cls.objects.filter(
            models.Q(sender=user1, receiver=user2, status='blocked') |
            models.Q(sender=user2, receiver=user1, status='blocked')
        ).exists()
    

class FriendshipNotification(models.Model):
    """
    Notifications for friend-related activities.
    """

    NOTIFICATION_TYPES = [
        ('friend_request', 'Friend Request'),
        ('request_accepted', 'Request Accepted'),
        ('request_declined', 'Request Declined')
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='friend_notifications'
    )
    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_notifications'
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    friendship = models.ForeignKey(
        Friendship,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} for {self.user.username}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()