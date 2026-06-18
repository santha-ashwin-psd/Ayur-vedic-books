import { ref } from "vue";
import { apiGET } from "../api/client.js";

export function useExchangeRate() {
  const rateLoading = ref(false);
  const rateSource  = ref(""); // "live" | "cache" | "stale" | "unavailable" | "error"
  const rateDate    = ref("");

  const SOURCE_LABELS = {
    live:        "🟢 Live",
    cache:       "🟡 Today",
    stale:       "🟠 Stale",
    unavailable: "⚪ No data",
    error:       "🔴 Error",
    identity:    "",
  };

  async function fetchRate(fromCurrency, toCurrency = "INR") {
    if (!fromCurrency || fromCurrency === toCurrency) {
      rateSource.value = "identity";
      return 1;
    }
    rateLoading.value = true;
    rateSource.value  = "";
    try {
      const res = await apiGET("zoho_books_clone.api.books_data.get_live_exchange_rate", {
        from_currency: fromCurrency,
        to_currency:   toCurrency,
      });
      rateSource.value = res?.source || "unknown";
      rateDate.value   = res?.date   || "";
      return res?.rate != null ? parseFloat(res.rate) : null;
    } catch {
      rateSource.value = "error";
      return null;
    } finally {
      rateLoading.value = false;
    }
  }

  function sourceLabel(src) {
    return SOURCE_LABELS[src || rateSource.value] || src || rateSource.value;
  }

  return { fetchRate, rateLoading, rateSource, rateDate, sourceLabel };
}
