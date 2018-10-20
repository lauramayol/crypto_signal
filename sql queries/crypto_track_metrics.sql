CREATE VIEW public."crypto_track_metrics"
AS
select * 
	, CASE WHEN t.btc_usd >0 THEN  (t.buy_bitcoin*1.0)/(t.btc_usd*1.0) END as trend_ratio
	, row_number() over (ORDER BY c.period_start_timestamp desc) rw_num
from crypto_track_cryptocandle c
left join crypto_track_pytrends t
on date(left(c.period_start_timestamp, 10)) = t.date
