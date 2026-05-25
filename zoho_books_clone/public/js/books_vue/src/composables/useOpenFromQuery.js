// Cross-document deep-link helper.
//
// Drop into any list page that has an "open the view drawer for record X"
// function. The composable:
//   1. After the initial `load()` resolves, checks if `?open=NAME` is in the URL
//      and triggers the open handler.
//   2. Watches the query so back/forward and in-app navigation keep working.
//
// Usage:
//   import { useOpenFromQuery } from "../composables/useOpenFromQuery.js";
//   ...
//   onMounted(async () => {
//     await load();
//     useOpenFromQuery({
//       list: () => list.value,             // reactive list getter
//       openByName: (name) => {
//         const r = list.value.find(x => x.name === name);
//         if (r) openView(r);
//       },
//     });
//   });

import { watch } from "vue";
import { useRoute } from "vue-router";

export function useOpenFromQuery({ list, openByName, paramKey = "open" } = {}) {
  const route = useRoute();

  const tryOpen = (name) => {
    if (!name || typeof openByName !== "function") return;
    // If the list isn't yet loaded, openByName may not find a row — caller
    // should ensure load() has resolved before invoking this composable.
    openByName(String(name));
  };

  // Fire once for the current query (handles initial mount + page refresh).
  tryOpen(route.query?.[paramKey]);

  // Keep working across in-app navigation (clicking a DocLink that points to
  // the same page, e.g. SO → SO inside the same list).
  const stop = watch(
    () => route.query?.[paramKey],
    (next) => {
      if (next) tryOpen(next);
    }
  );

  return { stop };
}
