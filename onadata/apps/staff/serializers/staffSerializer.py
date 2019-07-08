from __future__ import unicode_literals
import json
from rest_framework import serializers
from onadata.apps.staff.models import Staff, Attendance, Team, Bank
from onadata.apps.users.serializers import UserSerializer
from rest_framework.exceptions import ValidationError
from django.contrib.gis.geos import Point

class BankSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bank
        fields = ('id', 'name', )

class TeamSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team
        fields = ('id', 'name', )


class StaffSerializer(serializers.ModelSerializer):
    designation_label = serializers.CharField(source='get_designation_display', read_only=True)

    class Meta:
        model = Staff
        # exclude = ('created_by', 'team', 'created_date', 'updated_date', 'is_deleted',)
        fields = ('id', 'first_name', 'last_name', 'email', 'gender', 'ethnicity', 'address', 'phone_number', 'bank_name',
                  'account_number', 'photo', 'date_of_birth', 'contract_start', 'contract_end', 'IdPassDID',
                  'bank', 'designation', 'designation_label')

    def create(self, validated_data):
        bank_id = validated_data.pop('bank') if 'bank' in validated_data else None
        
        instance = Staff.objects.create(**validated_data)
        try:
            if bank_id:
                instance.bank = bank_id
                instance.bank_name = ''

            else:
                if instance.bank_name == "":
                    raise ValidationError("Got empty bank name. Provide either bank id or bank name.")     
            instance.save()
        
        except Exception as e:
            raise ValidationError("Got error on: {}".format(e))

        return instance

class AttendanceSerializer(serializers.ModelSerializer):
    latitude = serializers.CharField(write_only=True, required=False)
    longitude = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Attendance
        exclude = ('created_date', 'updated_date', 'submitted_by', 'team', 'is_deleted')
        read_only_fields = ('location',)

    def create(self, validated_data):
        try:

            staffs = validated_data.pop('staffs') if 'staffs' in validated_data else []
            
            if 'latitude' in validated_data and 'longitude' in validated_data:
                p = Point(float(validated_data.pop('longitude')), float(validated_data.pop('latitude')), srid=4326)
                validated_data.update({'location':p})
            # else:
            #     raise ValidationError("No location coordinates provided.")

            if not staffs:
                raise ValidationError("Got Empty staffs list.")

            else:
                for staff in staffs:
                    if int(staff.team_id) != int(validated_data.get('team_id')):            
                        raise ValidationError("Got error on: Staffs entered has different team.")
            
            instance = Attendance.objects.create(**validated_data)
            instance.staffs = staffs
            instance.save()
        
        except Exception as e:
            raise ValidationError("Got error on: {}".format(e))

        else:
            return instance




