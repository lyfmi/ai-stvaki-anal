export type TabId = "home" | "history" | "profile";

export type Route =
  | { type: "home" }
  | { type: "history" }
  | { type: "profile" }
  | { type: "analyzeResult"; id: string }
  | { type: "unlimited" }
  | { type: "support" }
  | { type: "admin" };

export const homeRoot: Route = { type: "home" };
export const historyRoot: Route = { type: "history" };
export const profileRoot: Route = { type: "profile" };

export function routeKey(route: Route): string {
  switch (route.type) {
    case "analyzeResult":
      return `analyzeResult:${route.id}`;
    default:
      return route.type;
  }
}

export function isRootRoute(route: Route): boolean {
  return route.type === "home" || route.type === "history" || route.type === "profile";
}
