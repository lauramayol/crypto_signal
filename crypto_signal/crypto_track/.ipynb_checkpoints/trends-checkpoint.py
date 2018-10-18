from pytrends.request import TrendReq

kw_list = ['buy bitcoin']

pytrends = TrendReq(hl='en - US')
# print(pytrends.interest_over_time(kw_list))

kw_list = ['buy bitcoin']
print(pytrends.build_payload(kw_list, cat=0, timeframe='today 5-y', geo='', gprop='')
      )
print(kw_list)
