# coding=utf-8

from django.shortcuts import render
from python_sdk.src.openapi_client import openapi_client as client
from python_sdk.src.core.rsa_client import rsa_client as rsa
import os
import json
import xmltodict
from pandas import DataFrame
# 导入R脚本
import rpy2.rlike.container as rlc
import rpy2.robjects as rob
from rpy2.robjects import pandas2ri

appid = ""

# Create your views here.


"""  ======散标列表====== """


def showProductList(request):
    access_url = "http://gw.open.ppdai.com/invest/LLoanInfoService/LoanList"
    data = {
        "PageIndex": 1,
        "StartDateTime": "2000-01-01 00:00:00.000"
    }
    sort_data = rsa.sort(data)
    sign = rsa.sign(sort_data)
    list_result = client.send(access_url, json.dumps(data), appid, sign)
    returnValue = xmltodict.parse(list_result)

    if int(returnValue['LLoanListResponse']['Result']) == 1:  # 成功
        pList = []
        loanInfos = returnValue['LLoanListResponse']['LoanInfos']['LLoanInfo']

        for i in range(len(loanInfos)):
            pList.append(dict(loanInfos[i]))
    else:
        pList = []

    return render(request, 'productList.html', locals())


"""  ======计算结果====== """


def getResult(request):
    # 获取所有的待计算数据， 并转成R可以读取的格式
    ListingId = request.POST.getlist('ListingId', [])
    Title = request.POST.getlist('Title', [])
    inputAmount = request.POST['inputAmount']
    Months = request.POST.getlist('Months', [])
    CreditCode = request.POST.getlist('CreditCode', [])
    Rate = request.POST.getlist('Rate', [])
    data = rlc.OrdDict([('ListingId', rob.StrVector(ListingId)),
                        ('Title', rob.StrVector(Title)),
                        ('inputAmount', rob.IntVector([inputAmount] * len(ListingId))),
                        ('Months', rob.IntVector(Months)),
                        ('CreditCode', rob.StrVector(CreditCode)),
                        ('Rate', rob.FloatVector(Rate))])
    inputCalDataFrame = rob.DataFrame(data)
    """导入R"""
    rFilePath = os.path.dirname(os.path.abspath(__file__)) + '/DECISION.R'
    rob.r.source(rFilePath)
    decision = rob.globalenv['DECISION'](inputCalDataFrame)
    decisionDataFrame = pandas2ri.ri2py_dataframe(decision)  # 转为Python的DataFrame格式
    """/导入R """
    # 转换为输出结果
    inputAmount = list(decisionDataFrame['inputAmount'])[0]
    resultList = []
    for index, row in decisionDataFrame.iterrows():
        resultList.append(row.to_dict())

    return render(request, 'result.html', locals())
