from django.db import models

from boapp.models import Patient, Doctor


# Create your models here.

class MedicalRequest(models.Model):
    medical_request_idx = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    request_datetime = models.DateTimeField(null=False)
    req_able = models.CharField(max_length=1, null=False, default='Y')
    request_expire_datetime = models.DateTimeField(null=False)
    request_accept_yn = models.CharField(max_length=1, null=False, default='N')
