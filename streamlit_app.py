import streamlit as st
import pandas as pd


from helpers import is_email, QUERY_WORKER_ID, QUERY_TASK_ID, QUERY_WORKER_ROLE
from engine import get_safe_connection, run_query, get_tasks_metrics, sync_tasks, get_completed_tasks_for_worker


if 'worker_id' not in st.session_state:
    st.session_state.worker_id = None

if 'task_id' not in st.session_state:
    st.session_state.task_id = None

st.header("Worker id")

if st.session_state.worker_id is not None:
    st.info(f"Your 'Worker ID' is: {st.session_state.worker_id}")
    conn = get_safe_connection()

    role = run_query(conn, QUERY_WORKER_ROLE, worker_id=st.session_state.worker_id)
    role_str = role[0]['worker_role'] if len(role) > 0 else None
    
    if role_str is not None:
        st.info(f"Your role is: {role_str}")

    tasks = get_completed_tasks_for_worker(st.session_state.worker_id)
    if tasks and len(tasks) > 0:
        st.header("Your completed tasks")
        st.table(tasks)

    st.header("Task id")

    if st.session_state.task_id is not None:
        st.info(f"Your 'Task ID' is: {st.session_state.task_id}")
        with st.form("Submit your task id"):
            status = st.selectbox('Select status', ['Success', 'Fail', 'Platform Error'])
            comment = st.text_input('Enter your comment (if any)', "")

            submitted = st.form_submit_button("Submit task id", use_container_width=True)
            if submitted:
                tasks = get_tasks_metrics()    
                if len(tasks) == 0:
                    st.warning("We don't see this task as submitted, please wait and try to submit again")
                    st.stop()

                task = tasks[tasks['taskId'] == st.session_state.task_id]
                if task.empty:
                    st.warning("We don't see this task as submitted, please wait and try to submit again")
                    st.stop()

                task = task.iloc[0]
                conn = get_safe_connection()

                with conn.cursor() as cur:
                    cur.execute(f"""
                        UPDATE cyber_tasks SET 
                            worker_id = '{task['workerId']}',
                            succeeded = {task['succeeded']},
                            time_spent = {task['spentSeconds']},
                            labeler_comment = '{comment}',
                            reported_status = CAST('{status}' AS reported_status_enum_a0b4a657)
                        WHERE id = '{task['taskId']}'
                    """)
                    conn.commit()

                st.session_state.task_id = None
                st.experimental_rerun()
    else:
        with st.form("Get your task id"):
            submitted = st.form_submit_button("Get task id", use_container_width=True)
            if submitted:
                #sync_tasks()
                conn = get_safe_connection()
                task_id = run_query(conn, QUERY_TASK_ID, worker_id=st.session_state.worker_id)
                
                if len(task_id) == 0:
                    st.warning("No results found, if there won't be any results in 15 minutes it means that you have completed all tasks")
                    st.stop()

                st.session_state.task_id = task_id[0]['id']
                
                with conn.cursor() as cur:
                    cur.execute(f"UPDATE cyber_tasks SET distributed_at = NOW() WHERE id = '{st.session_state.task_id}'")
                    conn.commit()

                st.experimental_rerun()
else:
    with st.form("Get your worker id"):
        email = st.text_input('Enter your email', "example@domain.com")
        submitted = st.form_submit_button("Get worker id", use_container_width=True)
        if submitted:
            if not is_email(email):
                st.error("Please enter a valid email")
            else:
                conn = get_safe_connection()
                res = run_query(conn, QUERY_WORKER_ID, email=email)
                if len(res) == 0:
                    st.warning("No results found")
                    st.stop()
                st.session_state.worker_id = res[0]['truck_id']
                st.experimental_rerun()