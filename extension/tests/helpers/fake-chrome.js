import { vi } from "vitest";

/** A minimal, promise-based fake of the chrome.* APIs the extension uses.
 * Chrome MV3's real APIs return promises when no callback is passed — this
 * mock mirrors that, so the extension's own promise-based code (no
 * callback style anywhere) runs unmodified in tests. */
export function createFakeChrome() {
  const listeners = {
    runtimeOnMessage: [],
    runtimeOnInstalled: [],
    runtimeOnStartup: [],
    webNavigationOnCommitted: [],
    webNavigationOnHistoryStateUpdated: [],
    tabsOnRemoved: [],
    alarmsOnAlarm: [],
  };

  const storageData = { sync: {}, local: {} };

  function makeStorageArea(area) {
    return {
      async get(key) {
        if (key == null) return { ...storageData[area] };
        if (typeof key === "string") return { [key]: storageData[area][key] };
        return {};
      },
      async set(items) {
        Object.assign(storageData[area], items);
      },
      async remove(key) {
        delete storageData[area][key];
      },
      async clear() {
        storageData[area] = {};
      },
    };
  }

  const chrome = {
    __listeners: listeners,
    __storageData: storageData,
    storage: {
      sync: makeStorageArea("sync"),
      local: makeStorageArea("local"),
    },
    runtime: {
      sendMessage: vi.fn(async () => ({ ok: true })),
      onMessage: {
        addListener: (fn) => listeners.runtimeOnMessage.push(fn),
      },
      // Real Chrome only fires these on an actual install/update or a true
      // browser startup — never on every service-worker suspend/wake — so
      // the fake deliberately never auto-invokes them either; a test that
      // cares can call listeners.runtimeOnInstalled[0]()/OnStartup[0]()
      // itself.
      onInstalled: {
        addListener: (fn) => listeners.runtimeOnInstalled.push(fn),
      },
      onStartup: {
        addListener: (fn) => listeners.runtimeOnStartup.push(fn),
      },
      openOptionsPage: vi.fn(),
    },
    tabs: {
      query: vi.fn(async () => []),
      sendMessage: vi.fn(async () => ({})),
      create: vi.fn(async () => ({})),
      remove: vi.fn(async () => {}),
      reload: vi.fn(async () => {}),
      onRemoved: {
        addListener: (fn) => listeners.tabsOnRemoved.push(fn),
      },
    },
    webNavigation: {
      onCommitted: {
        addListener: (fn) => listeners.webNavigationOnCommitted.push(fn),
      },
      onHistoryStateUpdated: {
        addListener: (fn) => listeners.webNavigationOnHistoryStateUpdated.push(fn),
      },
    },
    cookies: {
      get: vi.fn(async () => null),
    },
    notifications: {
      create: vi.fn(async () => "notification-id"),
    },
    alarms: {
      create: vi.fn(),
      onAlarm: {
        addListener: (fn) => listeners.alarmsOnAlarm.push(fn),
      },
    },
    action: {
      setBadgeText: vi.fn(),
      setBadgeBackgroundColor: vi.fn(),
    },
  };

  return chrome;
}
