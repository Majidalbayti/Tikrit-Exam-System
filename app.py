import streamlit as st
import pandas as pd
import random
import io
from datetime import date

# 1. إعدادات الهوية البصرية لجامعة تكريت
st.set_page_config(page_title="نظام توزيع المراقبين - جامعة تكريت", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-header {
        background-color: #1b365d; 
        padding: 20px;
        border-radius: 15px;
        color: #ffffff;
        text-align: center;
        border-bottom: 6px solid #e5a93b;
        margin-bottom: 25px;
    }
    .main-header h1 { color: white !important; }
    .main-header h2 { color: #e5a93b !important; font-size: 2.2em; font-weight: bold; }
    .stButton>button {
        background-color: #1b365d; color: #e5a93b; border-radius: 8px; border: 2px solid #e5a93b; font-weight: bold; width: 100%;
    }
    .stButton>button:hover { background-color: #e5a93b; color: #1b365d; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <div class="main-header">
        <h1>جامعة تكريت</h1>
        <h2>كلية علوم الحاسوب والرياضيات </h2>
    </div>
    """, unsafe_allow_html=True)

# 2. عرض الشعار في القائمة الجانبية
try:
    st.sidebar.image("final-ccsm-01.jpg", use_container_width=True)
except:
    st.sidebar.markdown("🏛️ **كلية علوم الحاسوب والرياضيات**")

# 3. أداة رفع الملفات (File Uploader)
st.sidebar.header("📁 خطوة 1: ارفع ملف البيانات")
uploaded_file = st.sidebar.file_uploader("اختر ملف Excel يحتوي على شيتات (الأساتذة، القاعات)", type=["xlsx"])

# تهيئة مخزن المواعيد
if 'schedule_data' not in st.session_state:
    st.session_state['schedule_data'] = pd.DataFrame(columns=['التاريخ', 'عدد القاعات'])

if uploaded_file is not None:
    # قراءة البيانات من الملف المرفوع
    try:
        teachers_df = pd.read_excel(uploaded_file, sheet_name="الأساتذة")
        halls_df = pd.read_excel(uploaded_file, sheet_name="القاعات")
        teachers_df.columns = teachers_df.columns.str.strip()
        halls_df.columns = halls_df.columns.str.strip()

        st.success("✅ تم تحميل بيانات الأساتذة والقاعات بنجاح!")

        # --- واجهة بناء المواعيد ---
        st.subheader("🗓️ خطوة 2: حدد مواعيد الامتحانات")
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            date_val = st.date_input("تاريخ الامتحان", value=date.today())
        with c2:
            halls_count = st.number_input("عدد القاعات", min_value=1, max_value=len(halls_df), value=1)
        with c3:
            st.write("")
            st.write("")
            if st.button("➕ إضافة"):
                new_row = pd.DataFrame({'التاريخ': [str(date_val)], 'عدد القاعات': [int(halls_count)]})
                st.session_state['schedule_data'] = pd.concat([st.session_state['schedule_data'], new_row],
                                                              ignore_index=True).drop_duplicates()
                st.rerun()

        if not st.session_state['schedule_data'].empty:
            edited_schedule = st.data_editor(st.session_state['schedule_data'], num_rows="dynamic",
                                             use_container_width=True)

            # --- إعدادات التوزيع ---
            st.sidebar.divider()
            senior_titles = st.sidebar.multiselect("ألقاب مدراء القاعات:",
                                                   ["ا.د.", "ا.م.د.", "م.د.", "أستاذ", "أستاذ مساعد", "مدرس دكتور"],
                                                   default=["ا.د.", "ا.م.د."])

            all_profs = teachers_df['اسم الأستاذ'].dropna().unique().tolist()
            target_prof = st.sidebar.selectbox("تخصيص تدريسي معين:", ["لا يوجد"] + all_profs)
            selected_dates = []
            if target_prof != "لا يوجد":
                selected_dates = st.sidebar.multiselect(f"أيام تواجد {target_prof}:",
                                                        options=edited_schedule['التاريخ'].tolist())

            if st.sidebar.button("🚀 توليد الجدول النهائي"):
                assigned_counts = {name: 0 for name in all_profs}
                final_output = []
                potential_managers = [t for t in all_profs if any(title in str(t) for title in senior_titles)]

                for _, row in edited_schedule.iterrows():
                    curr_date = str(row['التاريخ'])
                    num_halls = int(row['عدد القاعات'])
                    daily_taken = []

                    for h_idx in range(num_halls):
                        hall_info = halls_df.iloc[h_idx]
                        h_name = hall_info['اسم القاعة']
                        needed_total = int(hall_info['عدد المراقبين'])
                        hall_staff = []

                        # اختيار المدير
                        managers = [t for t in potential_managers if t not in daily_taken and (
                                    target_prof == "لا يوجد" or t != target_prof or curr_date in selected_dates)]
                        if managers:
                            managers.sort(key=lambda x: assigned_counts[x])
                            boss = managers[0]
                            hall_staff.append(boss)
                            daily_taken.append(boss)
                            assigned_counts[boss] += 1

                        # اختيار المراقبين
                        others = [t for t in all_profs if t not in daily_taken and (
                                    target_prof == "لا يوجد" or t != target_prof or curr_date in selected_dates)]
                        random.shuffle(others)
                        others.sort(key=lambda x: assigned_counts[x])
                        for s in others[:(needed_total - len(hall_staff))]:
                            hall_staff.append(s)
                            daily_taken.append(s)
                            assigned_counts[s] += 1

                        if hall_staff:
                            entry = {"التاريخ": curr_date, "القاعة": h_name, "مدير القاعة": hall_staff[0]}
                            for i, s_name in enumerate(hall_staff[1:]):
                                entry[f"مراقب {i + 2}"] = s_name
                            final_output.append(entry)

                st.session_state['final_result'] = pd.DataFrame(final_output)
                st.session_state['stats_df'] = pd.DataFrame(list(assigned_counts.items()),
                                                            columns=['الاسم', 'المراقبات']).sort_values(by='المراقبات',
                                                                                                        ascending=False)

        # --- العرض والتصدير ---
        if 'final_result' in st.session_state:
            st.divider()
            t1, t2 = st.tabs(["📝 الجدول النهائي", "📊 إحصائيات العدالة"])
            with t1:
                st.dataframe(st.session_state['final_result'], use_container_width=True)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    st.session_state['final_result'].to_excel(writer, index=False, sheet_name='الجدول')
                    st.session_state['stats_df'].to_excel(writer, index=False, sheet_name='إحصائية')
                st.download_button("📥 تحميل التقرير النهائي (Excel)", output.getvalue(),
                                   f"توزيع_امتحانات_تكريت_{date.today()}.xlsx")
            with t2:
                st.bar_chart(st.session_state['stats_df'].set_index('الاسم'))
    except Exception as e:
        st.error(f"❌ حدث خطأ في معالجة الملف: {e}. تأكد من أسماء الشيتات (الأساتذة، القاعات).")
else:
    st.info("👋 مرحباً بك! يرجى رفع ملف الإكسل من القائمة الجانبية للبدء.")
