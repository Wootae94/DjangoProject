from django.db import models


# Create your models here.

class PowerOfTwoAutoField(models.AutoField):
    def db_type(self, connection):
        return 'serial'  # 또는 'integer'를 사용할 수도 있음

    def get_internal_type(self):
        return 'PowerOfTwoAutoField'


class Hospital(models.Model):
    hospital_idx = models.AutoField(primary_key=True)
    hospital_name = models.CharField(max_length=255, null=False)


class Department(models.Model):
    department_idx = PowerOfTwoAutoField(primary_key=True)
    department_name = models.CharField(max_length=255, null=False)

    def save(self, *args, **kwargs):
        if not self.department_idx:
            # 새로운 레코드인 경우 department_num을 생성
            last_record = Department.objects.order_by('-department_idx').first()
            if last_record:
                self.department_idx = last_record.department_idx * 2
            else:
                self.department_idx = 1
        super().save(*args, **kwargs)


class NonInsuredTreatment(models.Model):
    treatment_idx = PowerOfTwoAutoField(primary_key=True)
    treatment_name = models.CharField(max_length=255, null=False)

    def save(self, *args, **kwargs):
        if not self.treatment_idx:
            # 새로운 레코드인 경우 treatment_idx를 생성
            last_record = NonInsuredTreatment.objects.order_by('-treatment_idx').first()
            if last_record:
                self.treatment_idx = last_record.treatment_idx * 2
            else:
                self.treatment_idx = 1
        super().save(*args, **kwargs)


class Doctor(models.Model):
    doctor_idx = models.AutoField(primary_key=True)
    doctor_name = models.CharField(max_length=255, null=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    # 2의 거듭제곱수의 합을 통해 비트 플래그 활용
    doctor_department_num = models.IntegerField()
    doctor_non_insured_treatment_num = models.IntegerField()


class BusinessHours(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    day_of_week = models.IntegerField()  # 월, 화, 수, 목, 금, 토, 일
    biz_open_time = models.TimeField(null=True)
    biz_close_time = models.TimeField(null=True)
    lunch_start_time = models.TimeField(null=True)
    lunch_end_time = models.TimeField(null=True)


class Patient(models.Model):
    patient_idx = models.AutoField(primary_key=True)
    patient_name = models.CharField(max_length=255, null=False)
