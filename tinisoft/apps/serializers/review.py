"""
Review serializers.
"""
from rest_framework import serializers
from apps.models import ProductReview, ReviewHelpful
from apps.serializers.auth import UserSerializer


class ReviewHelpfulSerializer(serializers.ModelSerializer):
    """Review helpful vote serializer."""
    
    class Meta:
        model = ReviewHelpful
        fields = ['id', 'is_helpful', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductReviewSerializer(serializers.ModelSerializer):
    """Product review serializer."""
    customer = UserSerializer(read_only=True)
    helpful_count = serializers.IntegerField(read_only=True)
    has_voted_helpful = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductReview
        fields = [
            'id', 'product', 'customer', 'customer_name', 'customer_email',
            'rating', 'title', 'comment', 'status', 'helpful_count',
            'has_voted_helpful', 'images', 'verified_purchase',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'customer', 'status', 'helpful_count', 'created_at', 'updated_at']
    
    def get_has_voted_helpful(self, obj):
        """Kullanıcı bu yoruma oy vermiş mi?"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return ReviewHelpful.objects.filter(
                review=obj,
                customer=request.user
            ).exists()
        # IP adresinden kontrol et
        if request:
            ip_address = self._get_client_ip(request)
            if ip_address:
                return ReviewHelpful.objects.filter(
                    review=obj,
                    ip_address=ip_address
                ).exists()
        return False
    
    def _get_client_ip(self, request):
        """Client IP adresini al."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ProductReviewCreateSerializer(serializers.ModelSerializer):
    """Product review create serializer (authenticated tenant user)."""
    
    class Meta:
        model = ProductReview
        fields = [
            'rating', 'title', 'comment', 'images',
        ]
        # customer_name ve customer_email view'da otomatik alınır (authenticated user'dan)
    
    def validate_rating(self, value):
        """Rating 1-5 arası olmalı."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Puan 1-5 arası olmalıdır.")
        return value
    
    def validate_comment(self, value):
        """Comment zorunlu."""
        if not value or not value.strip():
            raise serializers.ValidationError("Yorum metni gereklidir.")
        return value.strip()


class ProductReviewUpdateSerializer(serializers.ModelSerializer):
    """Product review update serializer (admin)."""
    
    class Meta:
        model = ProductReview
        fields = ['status', 'approved_by', 'approved_at']
        read_only_fields = ['approved_by', 'approved_at']
    
    def update(self, instance, validated_data):
        """Update review status."""
        status = validated_data.get('status')
        if status == 'approved' and instance.status != 'approved':
            from django.utils import timezone
            instance.approved_at = timezone.now()
            instance.approved_by = self.context['request'].user
        
        return super().update(instance, validated_data)

