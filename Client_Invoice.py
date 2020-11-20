#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests as r
import pandas as pd
import streamlit as st
import mysql.connector
import datetime


# In[2]:


st.title("Homemade Invoice Generator - Individual")


# In[3]:


user_name = st.sidebar.text_input("Please enter database user name")
password = st.sidebar.text_input("Please enter database passsword", type="password")
today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)
start_date = st.sidebar.date_input('Start date', today)
end_date = st.sidebar.date_input('End date', tomorrow)
if start_date < end_date:
    st.success('Start date: `%s`\n\nEnd date:`%s`' % (start_date, end_date))
else:
    st.error('Error: End date must fall after start date.')


# In[ ]:


disp_id = st.text_input("Please enter dispatcher client id")
parasut_login = st.sidebar.text_input("Please enter Paraşüt username")
parasut_pass = st.sidebar.text_input("Please enter Paraşüt password", type="password")
parasaut_client_id = st.sidebar.text_input("Please enter Paraşüt client id", type="password")


# In[ ]:


start = start_date.strftime("%Y%m%d")
end = end_date.strftime("%Y%m%d")
today = today.strftime("%Y%m%d")


# In[ ]:


mydb = mysql.connector.connect(
  host="http://analytics.dostavista.net",
  port="3306",
  user=user_name,
  password=password,
  database="turkey"
)


# In[ ]:


payload = {
        "grant_type": "password",
        "username": parasut_login,
        "password": parasut_pass,
        "client_id": parasaut_client_id,
        "redirect_uri": "ietf:wg:oauth:2.0:oob"
    }


# In[ ]:


response = r.post('https://api.parasut.com/oauth/token', data=payload)
response_json = response.json()

token = response_json["access_token"]

headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}


# In[ ]:


mycursor = mydb.cursor(dictionary=True)

sql = "SELECT o.user_id, sum(o.payment) as payment, l.bank_name as parasut_id, l.address_legal_city as vergi_no, l.address_legal as address, l.address_actual as vergi_dairesi from orders o left join legal_persons l on l.user_id=o.user_id WHERE o.status_id='3' and o.finish_datetime between '"+start+"' and '"+end+"' and o.user_id='"+disp_id+"' group by user_id"

mycursor.execute(sql)

myresult = mycursor.fetchall()

for row in myresult:
    row["payment"] = float(row["payment"]*100/118)
    row["user_id"] = str(row["user_id"])
    row["vergi_no"] = str(row["vergi_no"])
    row["address"] = str(row["address"])
    row["vergi_dairesi"] = str(row["vergi_dairesi"])


# In[ ]:


def order_list(client_id):
    mycursor_2 = mydb.cursor()
    query = "SELECT order_id from orders WHERE user_id='"+client_id+"' and status_id='3' and finish_datetime between '"+start+"' and '"+end+"'"
    mycursor_2.execute(query)
    result = mycursor_2.fetchall()
    orders = [list(i) for i in result]
    orders_str = ' '.join([str(element) for element in orders]) 
    return(orders_str)


# In[ ]:


def product(client_id):
    #create product
        product = {
            "data": {
            "id": "",
            "type": "products",
            "attributes": {
            "code": "",
            "name": "Fatura döneminde tamamlanmış gönderiler: "+order_list(client_id),
            "unit:": 1,
            "vat_rate": 18.0,
            "sales_excise_duty": 0,
            "unit": "",
            "communications_tax_rate": 0,
            "list_price": 0,
            "list_price_in_trl": 0,
            "currency": "TRL",
            "buying_price": 0,
            "initial_stock_count": 0
            },
            "relationships": {
            }
            }
            }
        prod = r.post("https://api.parasut.com/v4/183239/products", headers=headers, json=product)
        prod_json = prod.json()
        product_id = prod_json["data"]["id"]
        return(product_id)
        


# In[ ]:


for row in myresult:
    row["order_ids"] = order_list(row["user_id"])
    row["product_id"] = product(row["user_id"])


# In[ ]:


for row in myresult:
    invoice = {
            "data": {
            "id": "",
            "type": "sales_invoices",
            "attributes": {
            "item_type": "invoice",
            "description": "Hizmet Bedeli",
            "issue_date": today,
            "due_date": today,
            "invoice_series": "",
            "currency": "TRL",
            "exchange_rate": 0,
            "withholding_rate": 0,
            "vat_withholding_rate": 0,
            "invoice_discount_type": "percentage",
            "invoice_discount": 0,
            "billing_address": row["address"],
            "billing_phone": "",
            "billing_fax": "",
            "tax_office": row["vergi_dairesi"],
            "tax_number": row["vergi_no"],
            "city": "",
            "district": "",
            "is_abroad": "",
            "order_no": "",
            "order_date": today,
            "shipment_addres": "",
            },
            "relationships": {
            "details": {
            "data": [
              {
                "id": "",
                "type": "sales_invoice_details",
                "attributes": {
                  "quantity": 1,
                  "unit_price": row["payment"],
                  "vat_rate": 18.0,
                  "discount_type": "percentage",
                  "discount_value": 0,
                  "excise_duty_type": "percentage",
                  "excise_duty_value": 0,
                  "communications_tax_rate": 0,
                  "description": ""
                },
                "relationships": {
                  "product": {
                    "data": {
                      "id": row["product_id"],
                      "type": "products"
                    }
                  }
                }
              }
            ]
            },
            "contact": {
            "data": {
              "id": row["parasut_id"],
              "type": "contacts"
            }
            },
            "category": {
            "data": {
              "id": "4901641",
              "type": "item_categories"
            }
            },
            "sales_offer": {
            "data": {
              "id": "",
              "type": "sales_offers"
            }
            }
            }
            }
            }
    inv = r.post("https://api.parasut.com/v4/183239/sales_invoices", headers=headers, json=invoice)
    inv_json = inv.json()
    st.write(row["user_id"], inv_json["data"]["id"])

