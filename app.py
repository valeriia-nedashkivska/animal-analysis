import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Аналіз даних", layout="wide")

st.title("🐾 Аналіз показників притулку для тварин")
st.markdown("""
Цей застосунок виконує аналіз даних притулку для тварин. 
Він допомагає відповісти на ключові питання:
- Яка доля тварин найпоширеніша?
- Як вік впливає на шанси усиновлення?
- Чи впливає стерилізація на результат?
""")

OUTCOME_TRANSLATION = {
    'Adoption': 'Усиновлення',
    'Transfer': 'Передача іншому закладу',
    'Return_to_owner': 'Повернення власнику',
    'Euthanasia': 'Евтаназія',
    'Died': 'Смерть'
}

SEX_TRANSLATION = {
    'Intact Male': 'Некастрований самець',
    'Intact Female': 'Нестерилізована самка',
    'Neutered Male': 'Кастрований самець',
    'Spayed Female': 'Стерилізована самка',
    'Unknown': 'Невідомо'
}

@st.cache_data
def load_file():
    df = pd.read_csv('pets.csv')

    df = df.rename(columns={
        'AnimalID': 'animal_id',
        'Name': 'name',
        'DateTime': 'date_time',
        'OutcomeType': 'outcome_type',
        'OutcomeSubtype': 'outcome_subtype',
        'AnimalType': 'animal_type',
        'SexuponOutcome': 'sex_upon_outcome',
        'AgeuponOutcome': 'age_upon_outcome',
        'Breed': 'breed',
        'Color': 'color'
    })

    def parse_age(age_str):
        if pd.isna(age_str): return 0
        try:
            parts = age_str.split()
            num = int(parts[0])
            unit = parts[1]
            if 'year' in unit:
                return num * 12
            elif 'month' in unit:
                return num
            elif 'week' in unit:
                return num // 4
            return 0
        except:
            return 0

    df['age_months'] = df['age_upon_outcome'].apply(parse_age)
    df = df.dropna(subset=['outcome_type'])

    return df

df = load_file()

def classify_age(months):
    if months < 12: return 'Junior'
    elif months < 36: return 'Young adult'
    elif months < 96: return 'Adult'
    else: return 'Senior'

def check_is_mix(breed_text):
    if 'Mix' in breed_text or '/' in breed_text: return 'Yes'
    return 'No'

df['age_group'] = df['age_months'].apply(classify_age)
df['is_mix'] = df['breed'].apply(check_is_mix)

st.sidebar.header("Фільтри")
selected_type = st.sidebar.multiselect("Виберіть тип тварини:", df['animal_type'].unique(),
                                       default=df['animal_type'].unique())

if not selected_type:
    filtered_df = df.copy()
else:
    filtered_df = df[df['animal_type'].isin(selected_type)]

filtered_df['outcome_type_ua'] = filtered_df['outcome_type'].map(OUTCOME_TRANSLATION).fillna(filtered_df['outcome_type'])
filtered_df['sex_upon_outcome_ua'] = filtered_df['sex_upon_outcome'].map(SEX_TRANSLATION).fillna(filtered_df['sex_upon_outcome'])

st.header("1. Огляд даних")
st.markdown("""
Цей розділ дає загальне уявлення про вибірку. 
Метрики дозволяють швидко оцінити обсяг даних та середній вік тварин у поточній вибірці. 
""")

col1, col2 = st.columns([1, 2])
with col1:
    st.metric("Кількість записів", filtered_df.shape[0])
    st.metric("Середній вік, місяців", round(filtered_df['age_months'].mean(), 1))
    st.metric("Найчастіший результат", filtered_df['outcome_type_ua'].mode()[0])

with col2:
    st.dataframe(filtered_df.head(5), width="stretch")

st.divider()

st.header("2. Конструювання ознак")
st.markdown("""
Створення нових ознак на основі існуючих для покращення аналізу.
- `age_group`: групує тварин за життєвими етапами.
- `is_mix`: визначає, чи є тварина змішаної породи, що може впливати на популярність.
""")

st.code("""
df['age_group'] = df['age_months'].apply(classify_age)
df['is_mix'] = df['breed'].apply(check_is_mix)
""", language='python')

st.write("Приклад перетворених даних:")
st.dataframe(filtered_df[['animal_id', 'age_months', 'age_group', 'sex_upon_outcome', 'is_mix']].head())

st.divider()

st.header("3. Візуалізація даних")
st.markdown("У цьому розділі шукаємо відповіді на питання за допомогою графіків.")
tab1, tab2, tab3 = st.tabs(["Розподіл результатів", "Вік та результат", "Вплив статусу"])

with tab1:
    st.subheader("Що стається з тваринами?")
    st.markdown("""
    Мета: зрозуміти загальну ефективність роботи притулку.
    Ця діаграма показує відсоткове співвідношення різних результатів перебування тварин.
    
    *Високий відсоток Усиновлення та Повернення власнику є позитивним показником.*
    """)
    fig_pie = px.pie(filtered_df, names='outcome_type_ua', title='Розподіл результатів', hole=0.4)
    st.plotly_chart(fig_pie, width="stretch")

with tab2:
    st.subheader("Залежність результату від вікової групи")
    st.markdown("""
    Мета: перевірити гіпотезу, чи легше прилаштувати молодих тварин.
    Графік порівнює абсолютну кількість результатів для кожної вікової категорії.

    *Зверніть увагу на групи Junior та Senior, зазвичай різниця в усиновленні найбільша.*
    """)
    age_order = ['Junior', 'Young adult', 'Adult', 'Senior']
    age_outcome = filtered_df.groupby(['age_group', 'outcome_type_ua']).size().reset_index(name='count')
    fig_bar = px.bar(age_outcome, x="age_group", y="count", color="outcome_type_ua",
                     title="Результати по вікових групах", barmode='group',
                     category_orders={'age_group': age_order})
    st.plotly_chart(fig_bar, width="stretch")


with tab3:
    st.subheader("Вплив статусу")
    st.markdown("""
    Мета: оцінити, чи впливає стерилізація/кастрація на результат.
    Використовуємо теплову карту (Heatmap), де кольором позначена ймовірність конкретного результату.
    
    *Числа показують частку від 0 до 1. Наприклад, 0.66 означає 66% ймовірності.*
    """)
    fig_heat, ax = plt.subplots(figsize=(6, 4))
    ct = pd.crosstab(filtered_df['sex_upon_outcome_ua'], filtered_df['outcome_type_ua'], normalize='index')
    sns.heatmap(ct, annot=True, cmap="YlGnBu", fmt=".2f", ax=ax)
    plt.title("Ймовірність результату залежно від статусу")
    plt.ylabel("")
    plt.xlabel("")
    st.pyplot(fig_heat)