const API_BASE_URL = "http://localhost:8000/api";

export async function generateReport(formData) {
  const response = await fetch(`${API_BASE_URL}/report/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(formData),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "Failed to generate report");
  }

  return response.json();
}
