from datetime import datetime


def parse_detail(items):
	temp = {
    "crawl_url" : items['crawl_url'],
    "search_key" : items['company_name'],
    "key" : items['secret_key'],
    "update_time" : items['update_time'],
    "company_name" : items['company_name'],
    "credit_code" : items['corporation_tax'],
    "credit_code2" : items['social_credit_code'],
    "enterprise_type" : items['company_tags'],
    "phone" : items['telphone'],
    "mail" : items['email'],
    "web" : items['website'],
    "abstract" : items['company_abstract'],
    "industry" : items['industry'],
    "enname" : items['company_enname'],
    "big_holder" : items['big_holder'],
    "investment_rate" : items['big_holder_investment_rate'],
    "subscribed_capital" : items['big_holder_investment'],
    "financing_infos" : items['financing_info'],
    "tax_level" : items['tax_level'],
	"year_report": [],
	"legal_person": items['legal_person'],
	"state": items['company_status'],
	"registered_capital": items['registered_capital'],
	"registered_time": items['registered_date'],
	"allow_date": items['approval_date'],
	"ic_num": items['register_number'],
	"org_code": items['organization_code'],
	"company_type": items['company_type'],
	"tax_num": items['social_credit_code'],
	"business_term": items['business_term'],
	"registration_authority": items['registration_authority'],
	"registered_addr": items['registered_address'],
	"manage_range": items['operation_scope'],
	"branch": [],
	"level": "branch",
	"crawl_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	}
	return temp


def parse_branch(items):
	temp = []
	if not any(items):
		return []
	for i in items:
		branch_url = 'https://www.tianyancha.com/company/' + i['branch_company_id']
		temp.append(branch_url)
	return temp

def parse_year_report(items):
	year_report = []
	if not any(items):
		return []
	for item in items:
		temp = {
			       "year" : item['year'],
		            "postalcode" : item['postalcode'],
		            "employees_num" : item['employee_nums'],
		            "total_assets" : item['total_assets'],
		            "total_equity" : item['total_equity'],
		            "total_salesquity" : item['total_salesquity'],
		            "total_sales" : item['total_tax'],
		            "net_profit" : item['net_profit']
		        }
		year_report.append(temp)
	return year_report
	



