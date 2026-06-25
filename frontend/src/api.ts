export type CaseRecord = {
  id: string;
  customerId: string;
  title: string;
  status: string;
  priority: string;
  summary: string;
};

export type Customer = {
  id: string;
  name: string;
  company: string;
  email: string;
  plan: string;
  healthScore: number;
  lastSeen: string;
  cases: CaseRecord[];
  history: string[];
};

export type ToolCall = {
  name: string;
  arguments: string;
  resultSummary: string;
};

export type AgentResponse = {
  answer: string;
  safetyStatus: string;
  toolCalls: ToolCall[];
};

const GRAPHQL_URL = import.meta.env.VITE_GRAPHQL_URL ?? "http://localhost:8000/graphql";

async function graphQL<T>(query: string, variables?: Record<string, unknown>): Promise<T> {
  const response = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, variables })
  });

  const payload = await response.json();
  if (!response.ok || payload.errors) {
    throw new Error(payload.errors?.[0]?.message ?? "GraphQL request failed");
  }
  return payload.data as T;
}

export async function fetchCustomers(): Promise<Customer[]> {
  const data = await graphQL<{ customers: Customer[] }>(`
    query Customers {
      customers {
        id
        name
        company
        email
        plan
        healthScore
        lastSeen
        history
        cases {
          id
          customerId
          title
          status
          priority
          summary
        }
      }
    }
  `);
  return data.customers;
}

export async function askAgent(customerId: string, message: string): Promise<AgentResponse> {
  const data = await graphQL<{ askAgent: AgentResponse }>(
    `
      mutation AskAgent($customerId: String!, $message: String!) {
        askAgent(request: { customerId: $customerId, message: $message }) {
          answer
          safetyStatus
          toolCalls {
            name
            arguments
            resultSummary
          }
        }
      }
    `,
    { customerId, message }
  );
  return data.askAgent;
}
