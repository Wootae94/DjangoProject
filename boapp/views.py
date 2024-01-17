from django.forms import model_to_dict
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from boapp.models import Hospital, Department, NonInsuredTreatment, Doctor, BusinessHours, Patient

nav_list = [
    {"href": "/bo/setting/hospital", "text": "Hospital"},
    {"href": "/bo/setting/department", "text": "Department"},
    {"href": "/bo/setting/non_insured", "text": "NonInsured"},
    {"href": "/bo/setting/doctor", "text": "Doctor"},
    {"href": "/bo/setting/patient", "text": "Patient"},

]


def model_list_to_dict_list(model_list):
    return [model_to_dict(instance) for instance in model_list]


def setting(request, id):
    global nav_list
    title = "Setting Page"
    day_list = ['월', '화', '수', '목', '금', '토', '일']

    context = {
        'title': title,
        'nav_list': nav_list,
        'nav_title': id,
        'data_list': None,
        'day_list': day_list
    }
    data_list = []
    if request.method == 'POST':
        name_setting = request.POST.get('name_setting')
        nav_id = request.POST.get('nav_id')
        if nav_id == 'hospital':
            new_hospital = Hospital()
            new_hospital.hospital_name = name_setting
            new_hospital.save()
        elif nav_id == 'department':
            new_department = Department()
            new_department.department_name = name_setting
            new_department.save()
        elif nav_id == 'non_insured':
            new_non_insured = NonInsuredTreatment()
            new_non_insured.treatment_name = name_setting
            new_non_insured.save()
        elif nav_id == 'doctor':
            new_doctor = Doctor()
            new_doctor.doctor_name = name_setting
            new_doctor.hospital_id = request.POST.get('hospital')

            department_list = request.POST.getlist('department[]')
            department_sum = sum(int(department) for department in department_list)
            new_doctor.doctor_department_num = department_sum

            non_insured_list = request.POST.getlist('non_insured[]')
            non_insured_sum = sum(int(non_insured) for non_insured in non_insured_list)
            new_doctor.doctor_non_insured_treatment_num = non_insured_sum
            new_doctor.save()
            saved_doctor_idx = new_doctor.doctor_idx
            for i in range(1, 8):  # 월요일(1)부터 일요일(7)까지
                # BusinessHours 모델 생성 및 저장
                business_hours = BusinessHours()
                business_hours.doctor_id = saved_doctor_idx
                business_hours.day_of_week = i
                if request.POST.get(f'open_time_{i}') != '' and request.POST.get(f'close_time_{i}') != '':
                    business_hours.biz_open_time = request.POST.get(f'open_time_{i}')
                    business_hours.biz_close_time = request.POST.get(f'close_time_{i}')
                if request.POST.get(f'start_time_{i}') != '' and request.POST.get(f'end_time_{i}') != '':
                    # LunchBreak 모델 생성 및 저장
                    business_hours.lunch_start_time = request.POST.get(f'start_time_{i}')
                    business_hours.lunch_end_time = request.POST.get(f'end_time_{i}')
                business_hours.save()
        elif nav_id == 'patient':
            new_patient = Patient()
            new_patient.patient_name = name_setting
            new_patient.save()
        return HttpResponseRedirect(reverse('boapp:setting', args=[id]))
    else:
        if id == 'hospital':
            data_list = model_list_to_dict_list(Hospital.objects.all())
        elif id == 'department':
            data_list = model_list_to_dict_list(Department.objects.all())
        elif id == 'non_insured':
            data_list = model_list_to_dict_list(NonInsuredTreatment.objects.all())
        elif id == 'doctor':
            hospital_list = model_list_to_dict_list(Hospital.objects.all())
            department_list = model_list_to_dict_list(Department.objects.all())
            non_insured_list = model_list_to_dict_list(NonInsuredTreatment.objects.all())
            context['hospital_list'] = hospital_list
            context['department_list'] = department_list
            context['non_insured_list'] = non_insured_list
            data_list = model_list_to_dict_list(Doctor.objects.all())
        elif id == 'patient':
            data_list = model_list_to_dict_list(Patient.objects.all())
        context['data_list'] = data_list
        return render(request, 'boapp/setting.html', context)
