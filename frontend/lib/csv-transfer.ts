type ApiEnvelope<T> = {
  data: T | null;
};

function isApiEnvelope<T>(value: unknown): value is ApiEnvelope<T> {
  return (
    typeof value === "object"
    && value !== null
    && Object.prototype.hasOwnProperty.call(value, "data")
  );
}

export function unwrapCsvTransferResponse<T>(value: unknown): T {
  if (isApiEnvelope<T>(value)) {
    if (value.data === null) {
      throw new Error("The transfer response did not include data");
    }
    return value.data;
  }
  return value as T;
}
