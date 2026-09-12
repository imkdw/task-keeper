from sqlalchemy import event, inspect

from app.services.task_service import get_task


def _count_queries(session):
    """세션에서 실제로 실행된 SQL 문장을 모읍니다."""
    queries: list[str] = []

    def listener(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement)

    event.listen(session.bind, "before_cursor_execute", listener)
    return queries, lambda: event.remove(session.bind, "before_cursor_execute", listener)


def test_list_tasks_no_n_plus_one(client, db_session):
    for i in range(3):
        res = client.post("/tasks", json={"title": f"할 일 {i}", "tags": [f"태그{i}"]})
        assert res.status_code == 201

    # 식별 맵에 남은 로딩 결과를 비워 실제 조회 쿼리가 나가게 만듭니다.
    db_session.expire_all()

    queries, stop = _count_queries(db_session)
    try:
        res = client.get("/tasks")
    finally:
        stop()

    assert res.status_code == 200
    assert len(res.json()) == 3
    # tasks 1회 + 태그 selectin 1회. lazy 로딩으로 돌아가면 task 개수만큼 늘어납니다.
    assert len(queries) == 2, "\n".join(queries)


def test_get_task_loads_tags_eagerly(client, db_session):
    res = client.post("/tasks", json={"title": "단건", "tags": ["개인", "긴급"]})
    task_id = res.json()["id"]

    db_session.expire_all()

    task = get_task(db_session, task_id)

    # 반환 시점에 태그가 이미 로딩돼 있어야 합니다.
    # lazy 로딩이면 여기서 unloaded에 남아 접근할 때 추가 쿼리가 나갑니다.
    assert "tags" not in inspect(task).unloaded
    assert {t.name for t in task.tags} == {"개인", "긴급"}
