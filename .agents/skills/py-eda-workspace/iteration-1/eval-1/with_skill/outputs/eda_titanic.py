import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
import os

# 1. 데이터 로드
df = pd.read_csv('../../../../../../data/titanic.csv')

# images 폴더 생성 확인
os.makedirs('images', exist_ok=True)

# 2. 데이터 탐색
print("### 상위 5개 행")
print(df.head())
print("\n### 하위 5개 행")
print(df.tail())
print("\n### 기본 정보")
df.info()
print(f"\n전체 행/열: {df.shape}")
print(f"중복 데이터 수: {df.duplicated().sum()}")

# 3. 기술통계 및 보고서 (수치형)
desc_num = df.describe()
print("\n### 수치형 변수 기술통계")
print(desc_num)

# 4. 기술통계 및 보고서 (범주형)
desc_cat = df.describe(include=['O'])
print("\n### 범주형 변수 기술통계")
print(desc_cat)

# 5. 시각화 (10개 이상)
# 1) Survived 빈도 (Univariate)
plt.figure(figsize=(8, 6))
df['Survived'].value_counts().plot(kind='bar', color=['red', 'blue'])
plt.title('생존자 빈도 (0: 사망, 1: 생존)')
plt.xlabel('생존 여부')
plt.ylabel('빈도')
plt.savefig('images/v1_survived_count.png')
plt.close()

# 2) Pclass 빈도 (Univariate)
plt.figure(figsize=(8, 6))
df['Pclass'].value_counts().sort_index().plot(kind='bar', color='skyblue')
plt.title('객실 등급별 빈도')
plt.xlabel('객실 등급')
plt.ylabel('빈도')
plt.savefig('images/v2_pclass_count.png')
plt.close()

# 3) Sex 빈도 (Univariate)
plt.figure(figsize=(8, 6))
df['Sex'].value_counts().plot(kind='bar', color=['pink', 'lightblue'])
plt.title('성별 빈도')
plt.xlabel('성별')
plt.ylabel('빈도')
plt.savefig('images/v3_sex_count.png')
plt.close()

# 4) Age 분포 (Univariate)
plt.figure(figsize=(10, 6))
df['Age'].hist(bins=20, color='gray', edgecolor='black')
plt.title('연령대 분포')
plt.xlabel('나이')
plt.ylabel('빈도')
plt.savefig('images/v4_age_dist.png')
plt.close()

# 5) Sex vs Survived (Bivariate)
plt.figure(figsize=(8, 6))
pd.crosstab(df['Sex'], df['Survived']).plot(kind='bar', stacked=True)
plt.title('성별에 따른 생존 여부')
plt.savefig('images/v5_sex_survived.png')
plt.close()

# 6) Pclass vs Survived (Bivariate)
plt.figure(figsize=(8, 6))
pd.crosstab(df['Pclass'], df['Survived']).plot(kind='bar', stacked=True)
plt.title('객실 등급에 따른 생존 여부')
plt.savefig('images/v6_pclass_survived.png')
plt.close()

# 7) Fare vs Survived (Bivariate)
plt.figure(figsize=(10, 6))
sns.boxplot(x='Survived', y='Fare', data=df)
plt.title('생존 여부에 따른 운임 분포')
plt.savefig('images/v7_fare_survived.png')
plt.close()

# 8) Age vs Fare vs Survived (Multivariate)
plt.figure(figsize=(10, 6))
plt.scatter(df['Age'], df['Fare'], c=df['Survived'], cmap='coolwarm', alpha=0.6)
plt.colorbar(label='Survived')
plt.title('나이, 운임 및 생존 관계')
plt.xlabel('나이')
plt.ylabel('운임')
plt.savefig('images/v8_age_fare_survived.png')
plt.close()

# 9) Embarked vs Survived (Bivariate)
plt.figure(figsize=(8, 6))
pd.crosstab(df['Embarked'], df['Survived']).plot(kind='bar')
plt.title('승선 항구에 따른 생존 여부')
plt.savefig('images/v9_embarked_survived.png')
plt.close()

# 10) Pclass vs Age vs Survived (Multivariate)
plt.figure(figsize=(10, 6))
sns.violinplot(x='Pclass', y='Age', hue='Survived', data=df, split=True)
plt.title('객실 등급, 나이 및 생존 관계')
plt.savefig('images/v10_pclass_age_survived.png')
plt.close()

# 6. Text 분석 (Name TF-IDF)
tfidf = TfidfVectorizer(max_features=30)
tfidf_matrix = tfidf.fit_transform(df['Name'].fillna(''))
words = tfidf.get_feature_names_out()
sums = tfidf_matrix.sum(axis=0)
data = []
for col, word in enumerate(words):
    data.append((word, sums[0, col]))
ranking = pd.DataFrame(data, columns=['word', 'tfidf']).sort_values('tfidf', ascending=False)

plt.figure(figsize=(12, 8))
plt.barh(ranking['word'], ranking['tfidf'], color='orange')
plt.gca().invert_yaxis()
plt.title('Name 컬럼 TF-IDF 상위 30개 키워드')
plt.savefig('images/v11_name_tfidf.png')
plt.close()

print("\n### TF-IDF 상위 30개 키워드 표")
print(ranking)
