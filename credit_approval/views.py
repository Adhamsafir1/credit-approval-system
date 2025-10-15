






from rest_framework.views import APIView



from rest_framework.response import Response



from rest_framework import status



from .models import Customer, Loan



from .serializers import CustomerSerializer, LoanSerializer



import datetime







class RegisterCustomer(APIView):



    def post(self, request):



        monthly_income = request.data.get('monthly_income')



        if not monthly_income:



            return Response({'error': 'monthly_income is required'}, status=status.HTTP_400_BAD_REQUEST)







        approved_limit = round(36 * monthly_income / 100000) * 100000







        data = {



            'first_name': request.data.get('first_name'),



            'last_name': request.data.get('last_name'),



            'monthly_salary': monthly_income,



            'approved_limit': approved_limit,



            'phone_number': request.data.get('phone_number'),



        }







        serializer = CustomerSerializer(data=data)



        if serializer.is_valid():



            customer = serializer.save()



            return Response(serializer.data, status=status.HTTP_201_CREATED)



        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)







class CheckEligibility(APIView):



    def post(self, request):



        customer_id = request.data.get('customer_id')



        loan_amount = request.data.get('loan_amount')



        interest_rate = request.data.get('interest_rate')



        tenure = request.data.get('tenure')







        try:



            customer = Customer.objects.get(customer_id=customer_id)



        except Customer.DoesNotExist:



            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)







        # Credit Score Calculation



        credit_score = 0







        # 1. Past Loans paid on time



        loans = Loan.objects.filter(customer=customer)



        total_emis_paid_on_time = sum([loan.emis_paid_on_time for loan in loans])



        total_tenure = sum([loan.tenure for loan in loans])



        if total_tenure > 0:



            credit_score += (total_emis_paid_on_time / total_tenure) * 20







        # 2. No of loans taken in past



        credit_score += min(len(loans), 5) * 5







        # 3. Loan activity in current year



        current_year = datetime.datetime.now().year



        loans_in_current_year = loans.filter(date_of_approval__year=current_year)



        credit_score += min(len(loans_in_current_year), 2) * 10







        # 4. Loan approved volume



        total_loan_amount = sum([loan.loan_amount for loan in loans])



        if total_loan_amount > customer.approved_limit:



            credit_score -= 10







        # 5. If sum of current loans of customer > approved limit of customer, credit score = 0



        current_loans = loans.filter(end_date__gte=datetime.date.today())



        sum_of_current_loans = sum([loan.loan_amount for loan in current_loans])



        if sum_of_current_loans > customer.approved_limit:



            credit_score = 0







        credit_score = max(0, min(100, credit_score))







        # Loan Eligibility



        approval = False



        corrected_interest_rate = interest_rate







        if credit_score > 50:



            approval = True



        elif 30 < credit_score <= 50:



            if interest_rate > 12:



                approval = True



            else:



                corrected_interest_rate = 12



        elif 10 < credit_score <= 30:



            if interest_rate > 16:



                approval = True



            else:



                corrected_interest_rate = 16



        else:



            approval = False







        if sum([loan.monthly_repayment for loan in current_loans]) > customer.monthly_salary * 0.5:



            approval = False







        response_data = {



            'customer_id': customer_id,



            'approval': approval,



            'interest_rate': interest_rate,



            'corrected_interest_rate': corrected_interest_rate,



            'tenure': tenure,



            'monthly_installment': loan_amount * (1 + corrected_interest_rate/100) / tenure if tenure > 0 else 0



        }







        return Response(response_data, status=status.HTTP_200_OK)







class CreateLoan(APIView):



    def post(self, request):



        customer_id = request.data.get('customer_id')



        loan_amount = request.data.get('loan_amount')



        interest_rate = request.data.get('interest_rate')



        tenure = request.data.get('tenure')







        # Run eligibility check



        eligibility_response = CheckEligibility().post(request)







        if not eligibility_response.data['approval']:



            return Response({'message': 'Loan not approved'}, status=status.HTTP_400_BAD_REQUEST)







        customer = Customer.objects.get(customer_id=customer_id)



        monthly_repayment = eligibility_response.data['monthly_installment']







        loan = Loan.objects.create(



            customer=customer,



            loan_amount=loan_amount,



            tenure=tenure,



            interest_rate=eligibility_response.data['corrected_interest_rate'],



            monthly_repayment=monthly_repayment,



            emis_paid_on_time=0,



            date_of_approval=datetime.date.today(),



            end_date=datetime.date.today() + datetime.timedelta(days=tenure * 30)



        )







        response_data = {



            'loan_id': loan.loan_id,



            'customer_id': customer.customer_id,



            'loan_approved': True,



            'message': 'Loan approved and created',



            'monthly_installment': monthly_repayment



        }







        return Response(response_data, status=status.HTTP_201_CREATED)







class ViewLoan(APIView):



    def get(self, request, loan_id):



        try:



            loan = Loan.objects.get(loan_id=loan_id)



            serializer = LoanSerializer(loan)



            customer_serializer = CustomerSerializer(loan.customer)



            response_data = serializer.data



            response_data['customer'] = customer_serializer.data



            return Response(response_data)



        except Loan.DoesNotExist:



            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)







class ViewCustomerLoans(APIView):



    def get(self, request, customer_id):



        try:



            customer = Customer.objects.get(customer_id=customer_id)



            loans = Loan.objects.filter(customer=customer)



            serializer = LoanSerializer(loans, many=True)



            return Response(serializer.data)



        except Customer.DoesNotExist:



            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)




