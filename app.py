import requests
import pandas as pd
import plotly.express as px
import asyncio
from shinywidgets import output_widget, render_widget

from shiny import App, reactive, render, req, ui

class Get_Data():
    def __init__(self):
        self.server_url = "http://localhost:5000/"

    def get_data(self, url="api/json"):
        request_url = f"{self.server_url}/{url}"
        response = requests.get(request_url)
        try:
            if response.status_code == 200:
                data = response.json()  
                df = pd.json_normalize(data)
            else:
                raise NotImplementedError
        except NotImplementedError:
            print("Probleme lors de la récupération des données.")
        return df
    
    def get_list_values(self, url):
        request_url = f"{self.server_url}/{url}"
        response = requests.get(request_url)
        try:
            if response.status_code == 200:
                list_values = response.json()
            else:
                raise NotImplementedError
        except NotImplementedError:
            print("Probleme lors de la récupération de la liste.")
        return list_values

data_getter = Get_Data()
df = data_getter.get_data()

app_ui = ui.page_fillable(
    ui.page_navbar(
        ui.nav_panel(
            "Résultats licences",
            ui.h2(
                "Interface graphique Projet INFO908: Taux de réussite en Licence.",
                style="background-color:#F0F8FF; font-weight:bold; font-size:18px; color:#1F618D; margin-top:0px;",
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header(
                        "Choisir les stats à afficher ",
                        ui.input_selectize("selec_global_licence",  None, {"gd_discipline": "Grandes disciplines", "discipline": "Disciplines"}),
                        full_screen=True
                    ),
                    output_widget("country_detail_pop"), 
                    height="400px",
                    ),
                col_widths=[12, 12],
            ),
        ),
        ui.nav_panel(
            "Etudes profils",
            ui.h2(
                "Analyse des facteurs influençant la réussite universitaire",
                style="background-color:#F0F8FF; font-weight:bold; font-size:18px; color:#1F618D; margin-top:0px;",
            ),
            ui.layout_columns(
                # Première ligne - Graphique seul
                ui.card(
                    ui.card_header("1. Impact du type de bac sur la réussite"),
                    output_widget("reussite_par_type_bac"),
                    height="400px",
                ),
                # Deuxième ligne - Deux graphiques côte à côte
                ui.layout_columns(
                    ui.card(
                        ui.card_header("2. Influence mention bac sur L2"),
                        output_widget("passage_l2_par_mention"),
                        height="400px",
                    ),
                    ui.card(
                        ui.card_header("3. Écart de réussite par genre"),
                       output_widget("reussite_par_sexe"),
                       height="400px",
                   ),
                   col_widths=[6, 6],  # 6 colonnes chacun = 50% de largeur
               ),
               col_widths=[12, 12],  # 12 colonnes = 100% de largeur pour chaque ligne
           ),
        ),
        ui.nav_panel(
            "Modèle",
            ui.card(
                ui.row(
                    ui.input_select("selec_gd_discipline", "Grande discipline:", data_getter.get_list_values(url="api/liste/gd_discipline")),#gd_disciple
                    ui.input_select("selec_discipline", "Discipline:", data_getter.get_list_values(url="api/liste/discipline")),#discipline
                    ui.input_select("selec_sect_disciplinaire", "Section disciplinaire:", data_getter.get_list_values(url="api/liste/secteurs_disciplinaire")),#sect_disciplinaire
                    ui.input_select("selec_serie_bac", "Serie bac:", data_getter.get_list_values(url="api/liste/types_bac")),#serie_bac
                ),
                ui.row(
                    ui.input_select("selec_age_au_bac", "Age obtention:", data_getter.get_list_values(url="api/liste/age_au_bac")), #age_au_bac
                    ui.input_select("selec_sexe", "Sexe:", data_getter.get_list_values(url="api/liste/sexe")),#sexe
                    ui.input_select("selec_mention_bac", "Mention:", data_getter.get_list_values(url="api/liste/mentions_bac")),#mention_bac
                    ui.input_select("selec_model_name", "Modele:", ["logistic", "rf"]),#model_name
                ),
                ui.row(
                    ui.input_task_button("button_infer_model", "Calculer le taux de réussite"),
                    ui.input_action_button("btn_cancel_infer", "Annuler"),
                ),
            ),
            ui.card(
                ui.output_text("resultat_infer_model")
            )
        ),
        ui.nav_panel(
            "DataFrame",
            ui.card(ui.output_data_frame("summary_data"), height="800px"),
        ),
    ),
)

def server(input, output, session):
    
    #Page Licence
    @render.data_frame
    def summary_data(): #Affichage dataframe 
        return render.DataGrid(data_getter.get_data().round(2), selection_mode="rows")

    @render_widget
    def country_detail_pop():
        selected_var = input.selec_global_licence()
        df_long = data_getter.get_data(url=f"api/taux_reussite_licence/{selected_var}").melt(var_name=selected_var, value_name="%")
        return px.bar(
            df_long, 
            x=selected_var, 
            y="%", 
            text="%", 
            title= f"Taux de réussite par {selected_var}.")


    #Page Details


    #Page Modele

    @ui.bind_task_button(button_id="button_infer_model")
    @reactive.extended_task
    async def infer_model(gd_discipline, discipline, sect_disciplinaire, serie_bac, age_au_bac, sexe, mention_bac, model_name):
        param_request = f"gd_discipline={gd_discipline}&discipline={discipline}&sect_disciplinaire={sect_disciplinaire}&serie_bac={serie_bac}&age_au_bac={age_au_bac}&sexe={sexe}&mention_bac={mention_bac}&model_name={model_name}"
        request = "ml/prediction_reussite"
        model_infer = data_getter.get_data(url=f"{request}?{param_request}")
        print(model_infer)
        return model_infer
    
    @reactive.effect
    @reactive.event(input.button_infer_model, ignore_none=False)
    def infer_model_click():
        gd_discipline = input.selec_gd_discipline()
        discipline = input.selec_discipline()
        sect_disciplinaire = input.selec_sect_disciplinaire()
        serie_bac = input.selec_serie_bac()
        age_au_bac = input.selec_age_au_bac()
        sexe = input.selec_sexe()
        mention_bac = input.selec_mention_bac()
        model_name = input.selec_model_name()
        print(gd_discipline)
        infer_model(gd_discipline, discipline, sect_disciplinaire, serie_bac, age_au_bac, sexe, mention_bac, model_name)

    @reactive.effect
    @reactive.event(input.btn_cancel_infer)
    def handle_cancel():
        infer_model.cancel()

    @render.text
    def resultat_infer_model():
        return str(infer_model.result())

    @render_widget
    def reussite_par_type_bac():
        # Récupération des données
        raw_data = data_getter.get_data(url="api/taux_reussite_licence/type_bac")
        df = pd.DataFrame(raw_data)
        
        # Normalisation des noms de colonnes
        df.columns = [col.replace("BAC ", "").strip().lower() for col in df.columns]
        
        # Transformation en format long
        df_long = df.melt(var_name="categorie", value_name="taux")
        
        # Création du graphique
        return px.bar(
            df_long,
            x="categorie",
            y="taux",
            color="categorie",
            title="Réussite par Catégorie de Bac",
            labels={"categorie": "Type de Bac", "taux": "Taux de Réussite (%)"}
        )

    @render_widget
    def passage_l2_par_mention():
        try:
            # Récupération des données brutes
            raw_data = data_getter.get_data(url="api/passage_l2/bac")
            
            # Conversion en Series pandas si nécessaire
            if isinstance(raw_data, pd.DataFrame):
                raw_data = raw_data.iloc[0]  # Prendre la première ligne si format DataFrame

            # Transformation en format adapté
            df = pd.DataFrame({
                'type_bac': [k.replace("BAC ", "") for k in raw_data.index],
                'count': raw_data.values
            })

            # Création du graphique
            fig = px.bar(
                df,
                x='type_bac',
                y='count',
                color='type_bac',
                title="Passage en L2 par type de bac",
                labels={'type_bac': 'Type de bac', 'count': "Nombre d'étudiants"},
                hover_data={'count': ':.0f'}
            )

            fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
            
            return fig

        except Exception as e:
            print(f"Erreur dans passage_l2_par_mention: {str(e)}")
            return px.scatter(title="Données indisponibles")

    @render_widget
    def reussite_par_sexe():
        # Récupération des données brutes
        raw_data = data_getter.get_data(url="api/passage_l2/sexe")
        
        # Transformation en DataFrame
        df = pd.DataFrame(raw_data)

        # Create a DataFrame with the correct format
        df = pd.DataFrame({
            'sexe': ['Femme', 'Homme'],
            'taux': [raw_data['Femme.taux_passage'][0], raw_data['Homme.taux_passage'][0]]  # Access the first element of the Series
        })
            
        # Création du camembert
        return px.pie(
            df,
            names='sexe',
            values='taux',
            hole=0.4,
            title="Taux de passage en L2 par genre",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            labels={'taux': 'Taux de passage (%)', 'sexe': 'Genre'}
        ).update_traces(
            textinfo='percent+label',
            texttemplate='%{label}<br>%{percent:.1%}',
            hovertemplate='<b>%{label}</b><br>Taux exact: %{value:.1f}%'
        )
                             
    # @output.render
    # def resultat_inder_model():
    #     return 

app = App(app_ui, server)
