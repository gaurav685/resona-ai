"use client";

import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import { api } from "@/lib/api";
import { useUser } from "@/lib/user-context";
import { Select } from "@/components/ui/Select";
import type { UserSummary } from "@/lib/types";

export function UserPicker() {
  const { userId, setUserId } = useUser();
  const [users, setUsers] = useState<UserSummary[] | null>(null);

  useEffect(() => {
    api
      .listUsers()
      .then((res) => {
        const sorted = [...res.users].sort((a, b) => a.user_id.localeCompare(b.user_id));
        setUsers(sorted);
        if (!userId && sorted.length > 0) setUserId(sorted[0].user_id);
      })
      .catch(() => setUsers([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex items-center gap-2">
      <Users className="h-4 w-4 hidden sm:block" style={{ color: "var(--text-muted)" }} />
      <Select
        value={userId ?? ""}
        onChange={(e) => setUserId(e.target.value)}
        aria-label="Demo listener"
        disabled={!users || users.length === 0}
      >
        {!users && <option>Loading listeners…</option>}
        {users?.length === 0 && <option>No listeners available</option>}
        {users?.map((u) => (
          <option key={u.user_id} value={u.user_id}>
            {u.user_id} ({u.n_events} plays)
          </option>
        ))}
      </Select>
    </div>
  );
}
