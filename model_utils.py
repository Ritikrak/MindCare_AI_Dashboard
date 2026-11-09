import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder


class MentalHealthPredictor:
    def __init__(self):
        self.numeric_cols = [
            "Study_Hours",
            "Age",
            "Avg_Daily_Usage_Hours",
            "Daily_Unlocks",
            "Physical_Activity_Hours",
            "Sleep_Hours_Per_Night",
        ]
        self.ordinal_values = ["Low", "Medium", "High", "Very High"]
        self.ordinal_map = {value: idx for idx, value in enumerate(self.ordinal_values)}
        self.category_cols = [
            "Gender",
            "Academic_Level",
            "Most_Used_Platform",
            "Purpose_Of_Use",
            "Grouped_country",
        ]
        self.gender_encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        self.academic_encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        self.platform_encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        self.purpose_encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        self.country_encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        self.model = RandomForestRegressor(random_state=42)
        self.top_countries = []

    def _group_country(self, country: str) -> str:
        return country if country in self.top_countries else "Other"

    def fit(self, rows):
        country_counts = {}
        for row in rows:
            country_counts[row["Country"]] = country_counts.get(row["Country"], 0) + 1
        self.top_countries = [
            country for country, _ in sorted(country_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
        ]

        X_numeric = []
        X_stress = []
        X_gender = []
        X_academic = []
        X_platform = []
        X_purpose = []
        X_country = []
        y = []

        for row in rows:
            grouped = self._group_country(row["Country"])
            X_numeric.append(
                [
                    float(row["Study_Hours"]),
                    int(row["Age"]),
                    float(row["Avg_Daily_Usage_Hours"]),
                    int(row["Daily_Unlocks"]),
                    float(row["Physical_Activity_Hours"]),
                    float(row["Sleep_Hours_Per_Night"]),
                ]
            )
            X_stress.append([self.ordinal_map[row["Stress_Level"]]])
            X_gender.append([row["Gender"]])
            X_academic.append([row["Academic_Level"]])
            X_platform.append([row["Most_Used_Platform"]])
            X_purpose.append([row["Purpose_Of_Use"]])
            X_country.append([grouped])
            y.append(float(row["Mental_Health_Score"]))

        self.gender_encoder.fit(np.array(X_gender, dtype=object))
        self.academic_encoder.fit(np.array(X_academic, dtype=object))
        self.platform_encoder.fit(np.array(X_platform, dtype=object))
        self.purpose_encoder.fit(np.array(X_purpose, dtype=object))
        self.country_encoder.fit(np.array(X_country, dtype=object))

        X = np.hstack(
            [
                np.array(X_numeric, dtype=float),
                np.array(X_stress, dtype=float),
                self.gender_encoder.transform(np.array(X_gender, dtype=object)),
                self.academic_encoder.transform(np.array(X_academic, dtype=object)),
                self.platform_encoder.transform(np.array(X_platform, dtype=object)),
                self.purpose_encoder.transform(np.array(X_purpose, dtype=object)),
                self.country_encoder.transform(np.array(X_country, dtype=object)),
            ]
        )
        self.model.fit(X, np.array(y, dtype=float))

    def _build_input(self, data):
        grouped = data["country"] if data["country"] in self.top_countries else "Other"
        numeric = np.array(
            [
                float(data["study_hours"]),
                int(data["age"]),
                float(data["avg_daily_usage_hours"]),
                int(data["daily_unlocks"]),
                float(data["physical_activity_hours"]),
                float(data["sleep_hours_per_night"]),
            ],
            dtype=float,
        ).reshape(1, -1)
        stress = np.array([[self.ordinal_map[data["stress_level"]]]], dtype=float)
        gender = np.array([[data["gender"]]], dtype=object)
        academic = np.array([[data["academic_level"]]], dtype=object)
        platform = np.array([[data["most_used_platform"]]], dtype=object)
        purpose = np.array([[data["purpose_of_use"]]], dtype=object)
        country = np.array([[grouped]], dtype=object)

        X = np.hstack(
            [
                numeric,
                stress,
                self.gender_encoder.transform(gender),
                self.academic_encoder.transform(academic),
                self.platform_encoder.transform(platform),
                self.purpose_encoder.transform(purpose),
                self.country_encoder.transform(country),
            ]
        )
        return X

    def predict(self, data):
        return self.model.predict(self._build_input(data))[0]
