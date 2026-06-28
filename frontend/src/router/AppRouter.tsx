import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  historyRoot,
  homeRoot,
  isRootRoute,
  profileRoot,
  routeKey,
  type Route,
  type TabId,
} from "./types";

type Stacks = Record<TabId, Route[]>;

const initialStacks: Stacks = {
  home: [homeRoot],
  history: [historyRoot],
  profile: [profileRoot],
};

interface AppRouterValue {
  activeTab: TabId;
  currentRoute: Route;
  navigate: (tab: TabId) => void;
  push: (route: Route) => void;
  pop: () => void;
  canGoBack: boolean;
}

const AppRouterContext = createContext<AppRouterValue | null>(null);

function rootForTab(tab: TabId): Route {
  if (tab === "home") return homeRoot;
  if (tab === "history") return historyRoot;
  return profileRoot;
}

export function AppRouterProvider({ children }: { children: ReactNode }) {
  const [activeTab, setActiveTab] = useState<TabId>("home");
  const [stacks, setStacks] = useState<Stacks>(initialStacks);

  const currentRoute = stacks[activeTab][stacks[activeTab].length - 1];
  const canGoBack = stacks[activeTab].length > 1;

  const navigate = useCallback((tab: TabId) => {
    setActiveTab(tab);
    setStacks((prev) => {
      if (prev[tab].length === 0) {
        return { ...prev, [tab]: [rootForTab(tab)] };
      }
      return prev;
    });
  }, []);

  const push = useCallback(
    (route: Route) => {
      setStacks((prev) => {
        const stack = prev[activeTab];
        const last = stack[stack.length - 1];
        if (routeKey(last) === routeKey(route)) return prev;
        return { ...prev, [activeTab]: [...stack, route] };
      });
    },
    [activeTab]
  );

  const pop = useCallback(() => {
    setStacks((prev) => {
      const stack = prev[activeTab];
      if (stack.length <= 1) return prev;
      return { ...prev, [activeTab]: stack.slice(0, -1) };
    });
  }, [activeTab]);

  const value = useMemo(
    () => ({ activeTab, currentRoute, navigate, push, pop, canGoBack }),
    [activeTab, currentRoute, navigate, push, pop, canGoBack]
  );

  return <AppRouterContext.Provider value={value}>{children}</AppRouterContext.Provider>;
}

export function useAppRouter() {
  const ctx = useContext(AppRouterContext);
  if (!ctx) throw new Error("useAppRouter must be used within AppRouterProvider");
  return ctx;
}

export { isRootRoute };
