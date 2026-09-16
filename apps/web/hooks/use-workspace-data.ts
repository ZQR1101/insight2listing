"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import * as api from "@/lib/api";

export interface DashboardData {
  workspaceId: string;
  projects: api.Project[];
  productsByProject: Record<string, api.Product[]>;
  reviewCounts: Record<string, number>;
  loading: boolean;
  error: string | null;
  reload: () => void;
  totals: {
    projects: number;
    products: number;
    reviews: number;
    pending: number;
  };
}

export function useWorkspaceData(): DashboardData {
  const [workspaceId, setWorkspaceId] = useState("");
  const [projects, setProjects] = useState<api.Project[]>([]);
  const [productsByProject, setProductsByProject] = useState<
    Record<string, api.Product[]>
  >({});
  const [reviewCounts, setReviewCounts] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const reload = useCallback(() => setTick((v) => v + 1), []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const ws = await api.getWorkspace();
        const list = await api.listProjects();
        if (cancelled) return;
        setWorkspaceId(ws.id);
        setProjects(list.items);

        const productsMap: Record<string, api.Product[]> = {};
        const counts: Record<string, number> = {};
        await Promise.all(
          list.items.map(async (p) => {
            const prods = await api.listProducts(p.id);
            const revs = await api.listReviews(p.id);
            if (cancelled) return;
            productsMap[p.id] = prods.items;
            counts[p.id] = revs.total;
          })
        );
        if (cancelled) return;
        setProductsByProject(productsMap);
        setReviewCounts(counts);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Unknown error");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [tick]);

  const totals = useMemo(() => {
    const products = Object.values(productsByProject).reduce(
      (n, list) => n + list.length,
      0
    );
    const reviews = Object.values(reviewCounts).reduce((n, c) => n + c, 0);
    const pending = projects.filter((p) =>
      ["DRAFT", "DATA_IMPORTED"].includes(p.status)
    ).length;
    return {
      projects: projects.length,
      products,
      reviews,
      pending,
    };
  }, [projects, productsByProject, reviewCounts]);

  return {
    workspaceId,
    projects,
    productsByProject,
    reviewCounts,
    loading,
    error,
    reload,
    totals,
  };
}