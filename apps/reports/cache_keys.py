"""Ключи кэша отчётов (отдельный модуль без импортов — чтобы не было циклических зависимостей)."""
KPI_KEY = "reports:kpi"
BY_CATEGORY_KEY = "reports:by_category"
BY_EXECUTOR_KEY = "reports:by_executor"
ALL_KEYS = (KPI_KEY, BY_CATEGORY_KEY, BY_EXECUTOR_KEY)
