"use client"

import * as React from "react"

import type {
  ToastActionElement,
  ToastProps,
} from "@/components/ui/toast"

const TOAST_LIMIT = 5
const TOAST_REMOVE_DELAY = 5000

type ToasterToast = ToastProps & {
  id: string
  title?: React.ReactNode
  description?: React.ReactNode
  action?: ToastActionElement
}

/**
 * State manager for toasts using React's context API
 * This allows for centralized toast management across the application
 */
const actionTypes = {
  ADD_TOAST: "ADD_TOAST",
  UPDATE_TOAST: "UPDATE_TOAST",
  DISMISS_TOAST: "DISMISS_TOAST",
  REMOVE_TOAST: "REMOVE_TOAST",
} as const

type ActionType = typeof actionTypes

interface State {
  toasts: ToasterToast[]
}

type Action =
  | {
      type: ActionType["ADD_TOAST"]
      toast: ToasterToast
    }
  | {
      type: ActionType["UPDATE_TOAST"]
      toast: Partial<ToasterToast>
      id: string
    }
  | {
      type: ActionType["DISMISS_TOAST"]
      toastId?: string
    }
  | {
      type: ActionType["REMOVE_TOAST"]
      toastId?: string
    }

interface ToastContextType extends State {
  toast: (props: Omit<ToasterToast, "id">) => string
  dismiss: (toastId?: string) => void
}

/**
 * Toast context for passing toast state and actions throughout the app
 */
const ToastContext = React.createContext<ToastContextType | undefined>(
  undefined
)

/**
 * Toast reducer function for managing toast state changes
 */
function toastReducer(state: State, action: Action): State {
  switch (action.type) {
    case actionTypes.ADD_TOAST:
      return {
        ...state,
        toasts: [action.toast, ...state.toasts].slice(0, TOAST_LIMIT),
      }

    case actionTypes.UPDATE_TOAST:
      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === action.id ? { ...t, ...action.toast } : t
        ),
      }

    case actionTypes.DISMISS_TOAST: {
      const { toastId } = action

      // If no ID is provided, dismiss all toasts
      if (toastId === undefined) {
        return {
          ...state,
          toasts: state.toasts.map((t) => ({
            ...t,
            open: false,
          })),
        }
      }

      // Find the toast by ID and set it to open: false
      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === toastId ? { ...t, open: false } : t
        ),
      }
    }

    case actionTypes.REMOVE_TOAST: {
      const { toastId } = action

      if (toastId === undefined) {
        return {
          ...state,
          toasts: [],
        }
      }

      // Remove a specific toast by ID
      return {
        ...state,
        toasts: state.toasts.filter((t) => t.id !== toastId),
      }
    }
  }
}

/**
 * Provider component that makes toast functionality available
 */
export function ToastProvider({
  children,
}: {
  children: React.ReactNode
}): JSX.Element {
  const [state, dispatch] = React.useReducer(toastReducer, {
    toasts: [],
  })

  const toast = React.useCallback(
    (props: Omit<ToasterToast, "id">) => {
      const id = crypto.randomUUID()

      const newToast = {
        ...props,
        id,
        open: true,
        onOpenChange: (open: boolean) => {
          if (!open) {
            dismiss(id)
          }
        },
      }

      dispatch({
        type: actionTypes.ADD_TOAST,
        toast: newToast,
      })

      return id
    },
    [dispatch]
  )

  const dismiss = React.useCallback(
    (toastId?: string) => {
      dispatch({
        type: actionTypes.DISMISS_TOAST,
        toastId,
      })
    },
    [dispatch]
  )

  const remove = React.useCallback(
    (toastId?: string) => {
      dispatch({
        type: actionTypes.REMOVE_TOAST,
        toastId,
      })
    },
    [dispatch]
  )

  React.useEffect(() => {
    const timeouts: ReturnType<typeof setTimeout>[] = []

    state.toasts.forEach((toast) => {
      if (toast.open === false) {
        timeouts.push(
          setTimeout(() => {
            remove(toast.id)
          }, TOAST_REMOVE_DELAY)
        )
      }
    })

    return () => {
      timeouts.forEach((timeout) => clearTimeout(timeout))
    }
  }, [state.toasts, remove])

  return (
    <ToastContext.Provider
      value={{
        ...state,
        toast,
        dismiss,
      }}
    >
      {children}
    </ToastContext.Provider>
  )
}

/**
 * Hook to access toast functionality
 * 
 * @returns Toast context with methods for creating and managing toasts
 */
export function useToast(): ToastContextType {
  const context = React.useContext(ToastContext)

  if (context === undefined) {
    throw new Error("useToast must be used within a ToastProvider")
  }

  return context
}

/**
 * Helper type for toast parameters
 */
export type { ToasterToast } 