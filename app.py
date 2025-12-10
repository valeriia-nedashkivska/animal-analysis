import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Аналіз даних")

st.title("🐾 Аналіз показників притулку для тварин")
st.markdown("""
Цей застосунок виконує попередній аналіз даних (EDA), візуалізацію та конструювання ознак 
для сфери догляду за тваринами.
""")

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

st.sidebar.header("Фільтри")
selected_type = st.sidebar.multiselect("Виберіть тип тварини:", df['animal_type'].unique(),
                                       default=df['animal_type'].unique())

if not selected_type:
    filtered_df = df.copy()
else:
    filtered_df = df[df['animal_type'].isin(selected_type)]

st.header("1. Огляд даних")
col1, col2 = st.columns(2)
col1.metric("Кількість записів", filtered_df.shape[0])
col1.metric("Середній вік (місяців)", round(filtered_df['age_months'].mean(), 1))
col2.dataframe(filtered_df.head(5))

st.header("2. Конструювання ознак")
st.markdown("Створення нових ознак на основі існуючих для покращення аналізу.")


def classify_age(months):
    if months < 12:
        return 'Junior'
    elif months < 36:
        return 'Young adult'
    elif months < 96:
        return 'Adult'
    else:
        return 'Senior'


def check_is_mix(breed_text):
    if 'Mix' or '/' in breed_text:
        return 'Yes'
    return 'No'

filtered_df['age_group'] = filtered_df['age_months'].apply(classify_age)

filtered_df['is_mix'] = filtered_df['breed'].apply(check_is_mix)

st.code("""
# нова колонка age_group з віковою категорією на основі віку в місяцях
df['age_group'] = df['age_months'].apply(classify_age)
# нова колонка is_mix, що визначає змішану породу на основі її назви
df['is_mix'] = df['breed'].apply(check_is_mix)
""", language='python')

st.write("Оновлений датасет:")
st.dataframe(filtered_df[['animal_id', 'age_months', 'age_group', 'sex_upon_outcome', 'is_mix']].head())

st.header("3. Візуалізація даних")
tab1, tab2, tab3 = st.tabs(["Розподіл результатів", "Вік та результат", "Вплив статусу"])

outcome_type_translation = {
    'Adoption': 'Усиновлення',
    'Transfer': 'Передача іншому закладу',
    'Return_to_owner': 'Повернення власнику',
    'Euthanasia': 'Евтаназія',
    'Died': 'Смерть'
}

filtered_df['outcome_type_ua'] = filtered_df['outcome_type'].map(outcome_type_translation).fillna(filtered_df['outcome_type'])

with tab1:
    st.subheader("Що стається з тваринами?")
    fig_pie = px.pie(filtered_df, names='outcome_type_ua', title='Розподіл результатів', hole=0.4)
    st.plotly_chart(fig_pie, width="stretch")

age_order = ['Junior', 'Young adult', 'Adult', 'Senior']

with tab2:
    st.subheader("Залежність результату від вікової групи")
    age_outcome = filtered_df.groupby(['age_group', 'outcome_type_ua']).size().reset_index(name='count')
    fig_bar = px.bar(age_outcome, x="age_group", y="count", color="outcome_type_ua",
                     title="Результати по вікових групах", barmode='group',
                     category_orders={'age_group': age_order})
    st.plotly_chart(fig_bar, width="stretch")

sex_translation = {
    'Intact Male': 'Некастрований самець',
    'Intact Female': 'Нестерилізована самка',
    'Neutered Male': 'Кастрований самець',
    'Spayed Female': 'Стерилізована самка',
    'Unknown': 'Невідомо'
}

filtered_df['sex_upon_outcome_ua'] = filtered_df['sex_upon_outcome'].map(sex_translation).fillna(filtered_df['sex_upon_outcome'])

with tab3:
    st.subheader("Вплив статусу")
    fig_heat, ax = plt.subplots()
    ct = pd.crosstab(filtered_df['sex_upon_outcome_ua'], filtered_df['outcome_type_ua'], normalize='index')
    sns.heatmap(ct, annot=True, cmap="YlGnBu", fmt=".2f", ax=ax)
    plt.title("Ймовірність результату")
    st.pyplot(fig_heat)