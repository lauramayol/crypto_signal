-- ----------------------------------------------------------------
--  VIEW crypto_track_metrics
-- ----------------------------------------------------------------

CREATE OR REPLACE VIEW public.crypto_track_metrics
AS
   SELECT curr.currency_traded,
          curr.currency_quoted,
          curr.period_interval,
          curr.period_start_timestamp,
          curr.period_close,
          prior.period_close AS prior_period_close,
          (curr.period_close - prior.period_close) AS net_diff_period_close,
          curr.is_partial,
          curr.btc_usd,
          curr.buy_bitcoin,
          curr.trend_ratio,
          CASE
             WHEN (    (curr.trend_ratio > 0.35)
                   AND ((curr.period_close - prior.period_close) >
                        (80)::NUMERIC))
             THEN
                'BUY'::TEXT
             ELSE
                'SELL'::TEXT
          END AS buy_signal
     FROM (
        crypto_track_merged curr
        LEFT JOIN crypto_track_merged prior
           ON ((curr.rw_num = (prior.rw_num - 1))));


