'use client';

import { useState, useCallback } from 'react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastMessage {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
}

let toastListeners: Array<(toasts: ToastMessage[]) => void> = [];
let toastsState: ToastMessage[] = [];

function notifyListeners() {
  toastListeners.forEach((listener) => listener([...toastsState]));
}

export const toast = {
  show: (type: ToastType, title: string, description?: string) => {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast: ToastMessage = { id, type, title, description };
    toastsState = [...toastsState, newToast];
    notifyListeners();

    setTimeout(() => {
      toast.dismiss(id);
    }, 4000);
  },
  success: (title: string, description?: string) => toast.show('success', title, description),
  error: (title: string, description?: string) => toast.show('error', title, description),
  warning: (title: string, description?: string) => toast.show('warning', title, description),
  info: (title: string, description?: string) => toast.show('info', title, description),
  dismiss: (id: string) => {
    toastsState = toastsState.filter((t) => t.id !== id);
    notifyListeners();
  },
};

export function useToast() {
  const [toasts, setToasts] = useState<ToastMessage[]>(toastsState);

  const subscribe = useCallback(() => {
    const listener = (newToasts: ToastMessage[]) => setToasts(newToasts);
    toastListeners.push(listener);
    return () => {
      toastListeners = toastListeners.filter((l) => l !== listener);
    };
  }, []);

  return { toasts, subscribe, dismiss: toast.dismiss };
}
