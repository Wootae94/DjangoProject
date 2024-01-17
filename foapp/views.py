from datetime import datetime, timedelta

from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from boapp.models import *
from foapp.models import MedicalRequest

nav_list = [
    {"href": "/fo/search", "text": "search"},
    {"href": "/fo/request", "text": "request"},
    {"href": "/fo/find_req", "text": "find_req"},

]


def model_list_to_dict_list(model_list):
    return [model_to_dict(instance) for instance in model_list]


def power_of_two_sum_components(num):
    # 음수는 2의 거듭제곱수들의 합으로 나타낼 수 없음
    if num < 0:
        return None

    # 숫자가 0이거나 1이면 해당 숫자 자체를 반환
    if num == 0:
        return [0]
    elif num == 1:
        return [1]

    # 숫자를 2진수로 변환하여 '1'의 위치를 확인
    binary_representation = bin(num)[2:][::-1]  # 뒤집어서 확인
    power_of_two_positions = [i for i, bit in enumerate(binary_representation) if bit == '1']

    # 2의 거듭제곱수의 합으로 표현하기
    components = [2 ** pos for pos in power_of_two_positions]

    return components


def get_next_business_day(current_date, doctor_idx):
    doctor_results = model_list_to_dict_list(BusinessHours.objects.filter(Q(doctor__doctor_idx=doctor_idx)))
    next_day = current_date + timedelta(days=1)

    while True:
        # 휴무 여부 확인
        is_holiday = any(
            result['day_of_week'] == (next_day.weekday() + 1) % 7 and (
                    result['biz_close_time'] is None)
            for result in doctor_results
        )

        if not is_holiday:
            return next_day

        next_day += timedelta(days=1)


def search(request):
    global nav_list
    title = "Search Page"

    if request.method == "GET":
        search_keyword = request.GET.get("q", "")
        search_date = request.GET.get("d", "")
        search_time = request.GET.get("t", "")

        context = {
            'title': title,
            'nav_list': nav_list,
            'search_keyword': search_keyword
        }

        if search_keyword != "":
            all_doctor_list = Doctor.objects.all()
            search_words = search_keyword.split()
            doctor_name_search_results = []
            for d in all_doctor_list:
                if any(word == d.doctor_name for word in search_words):
                    doctor_name_search_results.append(d.doctor_name)
            hospital_name_search_results = []

            for d in all_doctor_list:
                if any(word == d.hospital.hospital_name for word in search_words):
                    hospital_name_search_results.append(d.doctor_name)
            department_search_results = []

            for d in all_doctor_list:
                doctor_department_list = power_of_two_sum_components(d.doctor_department_num)
                department_results = Department.objects.filter(Q(department_name__in=search_words))
                if any(department_result.department_idx in doctor_department_list for department_result in
                       department_results):
                    department_search_results.append(d.doctor_name)

            non_insured_search_results = []

            for d in all_doctor_list:
                doctor_non_insured_list = power_of_two_sum_components(d.doctor_non_insured_treatment_num)
                non_insured_results = NonInsuredTreatment.objects.filter(Q(treatment_name__in=search_words))
                if any(non_insured_result.treatment_idx in doctor_non_insured_list for non_insured_result in
                       non_insured_results):
                    non_insured_search_results.append(d.doctor_name)

            # 비어있지 않은 리스트만 선택
            non_empty_lists = [result for result in
                               [doctor_name_search_results, hospital_name_search_results, department_search_results,
                                non_insured_search_results] if result]

            # 최소 한 개 이상의 비어있지 않은 리스트가 있을 때 교집합 계산
            if non_empty_lists:
                doctor_names = set(non_empty_lists[0])
                for results in non_empty_lists[1:]:
                    doctor_names &= set(results)
                context['data_list'] = list(doctor_names)
            else:
                context['data_list'] = []
        elif search_date != "" and search_time != "":
            date_object = datetime.strptime(search_date, "%Y-%m-%d")
            day_of_week = date_object.strftime("%w")
            doctor_results = model_list_to_dict_list(BusinessHours.objects.filter(Q(day_of_week=day_of_week)))
            time_to_check = datetime.strptime(search_time, '%H:%M').time()
            print(time_to_check)
            filtered_results = []
            doctor_names = []
            for result in doctor_results:
                biz_open_time = result['biz_open_time']
                biz_close_time = result['biz_close_time']
                lunch_start_time = result['lunch_start_time']
                lunch_end_time = result['lunch_end_time']
                if biz_open_time <= time_to_check < biz_close_time:
                    if lunch_start_time and lunch_end_time:
                        if lunch_start_time <= time_to_check < lunch_end_time:
                            pass
                        else:
                            filtered_results.append(result)
            for res in filtered_results:
                doctor_id = res['doctor']
                d = Doctor.objects.filter(Q(doctor_idx=doctor_id)).first()
                if d:
                    doctor_names.append(d.doctor_name)
            context['data_list'] = list(set(doctor_names))  # 중복된 결과를 제거

    return render(request, 'foapp/search.html', context)


def request(request):
    title = "Request Page"
    global nav_list

    context = {
        'title': title,
        'nav_list': nav_list,
    }

    if request.method == 'GET':
        patient_list = model_list_to_dict_list(Patient.objects.all())
        doctor_list = model_list_to_dict_list(Doctor.objects.all())
        context['patient_list'] = patient_list
        context['doctor_list'] = doctor_list
        medical_request_idx = request.GET.get("idx", "")
        if medical_request_idx:
            req_data = MedicalRequest.objects.filter(Q(medical_request_idx=medical_request_idx)).first()

            req_data_dict = model_to_dict(req_data)
            context['req_data'] = req_data_dict

            patient_name = req_data.patient.patient_name if req_data.patient else None
            doctor_name = req_data.doctor.doctor_name if req_data.doctor else None
            request_datetime = req_data_dict.get('request_datetime')
            request_expire_datetime = req_data_dict.get('request_expire_datetime')
            req_able = req_data_dict.get('req_able')
            context['patient_name'] = patient_name
            context['doctor_name'] = doctor_name
            context['req_able'] = req_able
            context['request_datetime'] = request_datetime
            context['request_expire_datetime'] = request_expire_datetime

        return render(request, 'foapp/request.html', context)
    else:
        patient_idx = request.POST.get('patient')
        doctor_idx = request.POST.get('doctor')
        req_date = request.POST.get('d')
        req_time = request.POST.get('t')
        requested_datetime = datetime.strptime(f"{req_date} {req_time}", "%Y-%m-%d %H:%M")
        doctor_results = model_list_to_dict_list(BusinessHours.objects.filter(Q(doctor__doctor_idx=doctor_idx)))
        req_able = ''
        for result in doctor_results:
            if result['day_of_week'] == requested_datetime.weekday() + 1:

                biz_open_time = result['biz_open_time']
                biz_close_time = result['biz_close_time']
                lunch_start_time = result['lunch_start_time']
                lunch_end_time = result['lunch_end_time']

                if (
                        biz_open_time
                        and biz_close_time
                        and lunch_start_time
                        and lunch_end_time
                        and biz_open_time <= requested_datetime.time() <= lunch_start_time
                        or lunch_end_time <= requested_datetime.time() <= biz_close_time
                ):
                    req_able = 'Y'
                else:
                    req_able = 'N'
        if req_able == 'Y':
            request_expire_datetime = requested_datetime + timedelta(minutes=20)
        else:
            nearest_business_hour_start = None
            for result in doctor_results:
                if result['day_of_week'] == requested_datetime.weekday() + 1:
                    biz_open_time = result['biz_open_time']
                    biz_close_time = result['biz_close_time']
                    lunch_start_time = result['lunch_start_time']
                    lunch_end_time = result['lunch_end_time']

                    if biz_open_time and biz_open_time > requested_datetime.time():
                        nearest_business_hour_start = biz_open_time
                        break
                    elif lunch_start_time and lunch_end_time and lunch_end_time >= requested_datetime.time() >= lunch_start_time:
                        nearest_business_hour_start = lunch_end_time
                        break
                    elif biz_close_time and biz_close_time < requested_datetime.time():
                        next_biz_day = get_next_business_day(requested_datetime, doctor_idx)
                        tmp_doctor_results = model_list_to_dict_list(
                            BusinessHours.objects.filter(Q(doctor__doctor_idx=doctor_idx)))
                        for tmp_result in tmp_doctor_results:
                            if tmp_result['day_of_week'] == next_biz_day.weekday() + 1:
                                next_biz_open_time = tmp_result['biz_open_time']
                                nearest_business_hour_start = datetime.combine(next_biz_day.date(),
                                                                               next_biz_open_time) + timedelta(
                                    minutes=15)
            if nearest_business_hour_start:
                request_expire_datetime = nearest_business_hour_start
        new_medical_request = MedicalRequest()
        new_medical_request.patient_id = patient_idx
        new_medical_request.doctor_id = doctor_idx
        new_medical_request.req_able = req_able
        new_medical_request.request_datetime = requested_datetime
        new_medical_request.request_expire_datetime = request_expire_datetime
        new_medical_request.save()
        return HttpResponseRedirect(reverse('foapp:request') + f'?idx={new_medical_request.pk}')


def find_req(request):
    title = "Find Request Page"

    global nav_list

    context = {
        'title': title,
        'nav_list': nav_list,
    }

    doctor_list = model_list_to_dict_list(Doctor.objects.all())
    context['doctor_list'] = doctor_list
    if request.method == 'GET':
        doctor_idx = request.GET.get("doctor", "")
        if doctor_idx:
            context['doctor_name'] = Doctor.objects.filter(Q(doctor_idx=doctor_idx)).first().doctor_name
            data_list = []
            request_results = MedicalRequest.objects.filter(
                Q(doctor__doctor_idx=doctor_idx) & Q(request_accept_yn='N')).all()
            for req_res in request_results:
                medical_req_idx = req_res.medical_request_idx
                patient_name = req_res.patient.patient_name if req_res.patient else None
                # doctor_name = req_res.doctor.doctor_name if req_res.doctor else None
                request_datetime = req_res.request_datetime  # Use dot notation here
                request_expire_datetime = req_res.request_expire_datetime  # Use dot notation here
                req_data = {}
                req_data['medical_req_idx'] = medical_req_idx
                req_data['patient_name'] = patient_name
                # req_data['doctor_name'] = doctor_name
                req_data['request_datetime'] = request_datetime
                req_data['request_expire_datetime'] = request_expire_datetime
                data_list.append(req_data)
            context['data_list'] = data_list
        return render(request, 'foapp/find_req.html', context)


def accept_req(request):
    title = "Accept Request Page"

    global nav_list

    context = {
        'title': title,
        'nav_list': nav_list,
    }
    if request.method == 'POST':
        medical_request_idx = request.POST.get('medical_request_idx')
        medical_request = get_object_or_404(MedicalRequest, medical_request_idx=medical_request_idx)
        medical_request.request_accept_yn = 'Y'
        medical_request.save()
        medical_req_idx = medical_request.medical_request_idx
        patient_name = medical_request.patient.patient_name if medical_request.patient else None
        request_datetime = medical_request.request_datetime
        request_expire_datetime = medical_request.request_expire_datetime

        req_data = {}
        req_data['medical_req_idx'] = medical_req_idx
        req_data['patient_name'] = patient_name
        # req_data['doctor_name'] = doctor_name
        req_data['request_datetime'] = request_datetime
        req_data['request_expire_datetime'] = request_expire_datetime
        return HttpResponseRedirect(reverse('foapp:accept_req') + f'?idx={medical_req_idx}')
    else:
        medical_req_idx = request.GET.get("idx", "")
        req_data = MedicalRequest.objects.filter(Q(medical_request_idx=medical_req_idx)).first()
        context['req_data'] = req_data
        return render(request, 'foapp/accept_req.html', context)
