export async function requireOk(response: Response, errorMessage: string): Promise<Response> {
  if (!response.ok) {
    throw new Error(`${errorMessage}: ${response.status}`);
  }

  return response;
}
