
import pandas as pd
from django.core.management.base import BaseCommand
from credit_approval.models import Customer, Loan

class Command(BaseCommand):
    help = 'Load data from Excel files into the database'

    def handle(self, *args, **options):
        # Load customer data
        try:
            customer_df = pd.read_excel('customer_data.xlsx')
            for _, row in customer_df.iterrows():
                Customer.objects.create(
                    customer_id=row['customer_id'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    phone_number=row['phone_number'],
                    monthly_salary=row['monthly_salary'],
                    approved_limit=row['approved_limit'],
                    current_debt=row['current_debt']
                )
            self.stdout.write(self.style.SUCCESS('Successfully loaded customer data.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('customer_data.xlsx not found.'))

        # Load loan data
        try:
            loan_df = pd.read_excel('loan_data.xlsx')
            for _, row in loan_df.iterrows():
                try:
                    customer = Customer.objects.get(customer_id=row['Customer ID'])
                    Loan.objects.create(
                        customer=customer,
                        loan_id=row['Loan ID'],
                        loan_amount=row['Loan Amount'],
                        tenure=row['Tenure'],
                        interest_rate=row['Interest Rate'],
                        monthly_repayment=row['Monthly payment'],
                        emis_paid_on_time=row['EMIs paid on Time'],
                        date_of_approval=row['Date of Approval'],
                        end_date=row['End Date']
                    )
                except Customer.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Customer with ID {row['Customer ID']} not found. Skipping loan {row['Loan ID']}."))
            self.stdout.write(self.style.SUCCESS('Successfully loaded loan data.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('loan_data.xlsx not found.'))
