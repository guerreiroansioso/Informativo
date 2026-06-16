import altair as alt
import pandas as pd
import streamlit as st


BRAZIL_STATES_GEOJSON_URL = (
    "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/"
    "public/data/brazil-states.geojson"
)


def build_data() -> pd.DataFrame:
    rows = [
        ("Acre", "AC", "Norte", 94, 9),
        ("Alagoas", "AL", "Nordeste", 168, 18),
        ("Amapa", "AP", "Norte", 73, 5),
        ("Amazonas", "AM", "Norte", 221, 24),
        ("Bahia", "BA", "Nordeste", 486, 52),
        ("Ceara", "CE", "Nordeste", 345, 31),
        ("Distrito Federal", "DF", "Centro-Oeste", 132, 10),
        ("Espirito Santo", "ES", "Sudeste", 156, 13),
        ("Goias", "GO", "Centro-Oeste", 284, 27),
        ("Maranhao", "MA", "Nordeste", 251, 29),
        ("Mato Grosso", "MT", "Centro-Oeste", 178, 16),
        ("Mato Grosso do Sul", "MS", "Centro-Oeste", 143, 12),
        ("Minas Gerais", "MG", "Sudeste", 512, 46),
        ("Para", "PA", "Norte", 302, 35),
        ("Paraiba", "PB", "Nordeste", 147, 14),
        ("Parana", "PR", "Sul", 338, 28),
        ("Pernambuco", "PE", "Nordeste", 374, 41),
        ("Piaui", "PI", "Nordeste", 116, 11),
        ("Rio de Janeiro", "RJ", "Sudeste", 421, 39),
        ("Rio Grande do Norte", "RN", "Nordeste", 129, 12),
        ("Rio Grande do Sul", "RS", "Sul", 296, 22),
        ("Rondonia", "RO", "Norte", 105, 8),
        ("Roraima", "RR", "Norte", 66, 4),
        ("Santa Catarina", "SC", "Sul", 218, 17),
        ("Sao Paulo", "SP", "Sudeste", 742, 61),
        ("Sergipe", "SE", "Nordeste", 91, 7),
        ("Tocantins", "TO", "Norte", 88, 6),
    ]

    data = pd.DataFrame(
        rows,
        columns=["estado", "uf", "regiao", "internacoes", "mortes"],
    )
    data["estado_uf"] = data["estado"] + " (" + data["uf"] + ")"
    data["taxa_mortes"] = (data["mortes"] / data["internacoes"] * 100).round(1)
    return data


def filter_data(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    st.sidebar.header("Filtros")

    regions = st.sidebar.multiselect(
        "Regioes",
        options=sorted(data["regiao"].unique()),
        default=sorted(data["regiao"].unique()),
    )

    metric = st.sidebar.radio(
        "Grafico",
        options=["Internacoes", "Mortes", "Comparativo"],
    )

    top_limit = st.sidebar.slider(
        "Quantidade de estados",
        min_value=5,
        max_value=len(data),
        value=12,
    )

    region_data = data[data["regiao"].isin(regions)].copy()
    sort_column = "mortes" if metric == "Mortes" else "internacoes"
    chart_data = region_data.sort_values(sort_column, ascending=False).head(top_limit)

    return chart_data, region_data, metric


def render_metrics(data: pd.DataFrame) -> None:
    total_internacoes = int(data["internacoes"].sum())
    total_mortes = int(data["mortes"].sum())
    average_rate = data["taxa_mortes"].mean() if not data.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Internacoes", f"{total_internacoes:,}".replace(",", "."))
    col2.metric("Mortes", f"{total_mortes:,}".replace(",", "."))
    col3.metric("Taxa media", f"{average_rate:.1f}%")


def render_chart(data: pd.DataFrame, metric: str) -> None:
    if data.empty:
        st.warning("Nenhum estado encontrado para os filtros selecionados.")
        return

    state_order = data["estado_uf"].tolist()

    if metric == "Comparativo":
        chart_data = data.melt(
            id_vars=["estado_uf", "regiao", "taxa_mortes"],
            value_vars=["internacoes", "mortes"],
            var_name="indicador",
            value_name="casos",
        )
        chart_data["indicador"] = chart_data["indicador"].replace(
            {
                "internacoes": "Internacoes",
                "mortes": "Mortes",
            }
        )

        chart = (
            alt.Chart(chart_data)
            .mark_bar()
            .encode(
                x=alt.X("estado_uf:N", sort=state_order, title="Estado"),
                xOffset=alt.XOffset("indicador:N"),
                y=alt.Y("casos:Q", title="Casos"),
                color=alt.Color("indicador:N", title="Indicador"),
                tooltip=[
                    alt.Tooltip("estado_uf:N", title="Estado"),
                    alt.Tooltip("regiao:N", title="Regiao"),
                    alt.Tooltip("indicador:N", title="Indicador"),
                    alt.Tooltip("casos:Q", title="Casos", format=","),
                    alt.Tooltip("taxa_mortes:Q", title="Taxa de mortes", format=".1f"),
                ],
            )
            .properties(height=460)
        )
    else:
        column = "mortes" if metric == "Mortes" else "internacoes"
        color = "#b91c1c" if metric == "Mortes" else "#2563eb"

        chart = (
            alt.Chart(data)
            .mark_bar(color=color)
            .encode(
                x=alt.X("estado_uf:N", sort=state_order, title="Estado"),
                y=alt.Y(f"{column}:Q", title=metric),
                tooltip=[
                    alt.Tooltip("estado_uf:N", title="Estado"),
                    alt.Tooltip("regiao:N", title="Regiao"),
                    alt.Tooltip("internacoes:Q", title="Internacoes", format=","),
                    alt.Tooltip("mortes:Q", title="Mortes", format=","),
                    alt.Tooltip("taxa_mortes:Q", title="Taxa de mortes", format=".1f"),
                ],
            )
            .properties(height=460)
        )

    st.altair_chart(chart, width="stretch")


def render_map(data: pd.DataFrame, metric: str) -> None:
    if data.empty:
        st.warning("Nenhum estado encontrado para os filtros selecionados.")
        return

    map_metric = "mortes" if metric == "Mortes" else "internacoes"
    map_title = "Mortes" if map_metric == "mortes" else "Internacoes"
    map_color = "reds" if map_metric == "mortes" else "blues"
    states = alt.Data(
        url=BRAZIL_STATES_GEOJSON_URL,
        format=alt.DataFormat(property="features", type="json"),
    )

    lookup_data = data[
        ["uf", "estado", "regiao", "internacoes", "mortes", "taxa_mortes"]
    ]

    base = alt.Chart(states).mark_geoshape(
        fill="#f3f4f6",
        stroke="#d1d5db",
        strokeWidth=0.7,
    )

    highlighted = (
        alt.Chart(states)
        .mark_geoshape(stroke="#ffffff", strokeWidth=0.8)
        .transform_calculate(uf="datum.properties.sigla")
        .transform_lookup(
            lookup="uf",
            from_=alt.LookupData(
                lookup_data,
                "uf",
                ["estado", "regiao", "internacoes", "mortes", "taxa_mortes"],
            ),
        )
        .transform_filter("datum.internacoes != null")
        .encode(
            color=alt.Color(
                f"{map_metric}:Q",
                title=map_title,
                scale=alt.Scale(scheme=map_color),
            ),
            tooltip=[
                alt.Tooltip("estado:N", title="Estado"),
                alt.Tooltip("uf:N", title="UF"),
                alt.Tooltip("regiao:N", title="Regiao"),
                alt.Tooltip("internacoes:Q", title="Internacoes", format=","),
                alt.Tooltip("mortes:Q", title="Mortes", format=","),
                alt.Tooltip("taxa_mortes:Q", title="Taxa de mortes", format=".1f"),
            ],
        )
    )

    chart = (base + highlighted).project(type="mercator").properties(height=560)
    st.altair_chart(chart, width="stretch")


def main() -> None:
    st.set_page_config(
        page_title="Queimaduras no Brasil",
        page_icon=":bar_chart:",
        layout="wide",
    )

    data = build_data()
    chart_data, map_data, selected_metric = filter_data(data)

    st.title("Casos ficticios de queimaduras por estado")
    st.caption(
        "Dados demonstrativos para visualizacao: nao representam numeros oficiais."
    )

    render_metrics(map_data)
    st.subheader("Mapa por estado")
    render_map(map_data, selected_metric)

    st.subheader("Classificacao por estado")
    render_chart(chart_data, selected_metric)

    with st.expander("Ver dados usados no grafico"):
        st.dataframe(
            map_data[
                ["estado", "uf", "regiao", "internacoes", "mortes", "taxa_mortes"]
            ].sort_values("internacoes", ascending=False),
            width="stretch",
            hide_index=True,
        )


if __name__ == "__main__":
    main()
