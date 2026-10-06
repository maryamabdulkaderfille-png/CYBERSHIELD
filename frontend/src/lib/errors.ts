import { isAxiosError } from "axios";

import type { ApiErrorBody } from "@/types/auth";

export function extractErrorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (isAxiosError<ApiErrorBody>(error)) {
    const body = error.response?.data;
    if (body?.details) {
      const firstField = Object.values(body.details)[0];
      const firstMessage = Array.isArray(firstField) ? firstField[0] : undefined;
      if (firstMessage) return firstMessage;
    }
    if (body?.error) return body.error;
  }
  return fallback;
}
