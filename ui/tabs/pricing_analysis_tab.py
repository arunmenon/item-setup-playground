# File: ui/tabs/pricing_analysis_tab.py

import gradio as gr
import pandas as pd
import plotly.express as px
import json
import os

def create_pricing_analysis_tab():
    """
    Creates a Gradio tab for model pricing analysis:
      - Loads model pricing from an external JSON file
      - Allows filtering by provider, model substring
      - Accepts input tokens, output tokens, number of calls
      - Produces a DataFrame + bar chart of total cost
    """

    with gr.TabItem("Pricing Analysis"):
        gr.Markdown("## Model Pricing Analysis")

        # 1) Radio for calculating by tokens, words, or characters
        calc_by_selector = gr.Radio(
            ["Tokens", "Words", "Characters"],
            label="Calculate by:",
            value="Tokens"
        )

        # 2) Numeric fields for input tokens, output tokens, # of calls
        input_tokens = gr.Number(label="Input tokens", value=100, precision=0)
        output_tokens = gr.Number(label="Output tokens", value=500, precision=0)
        api_calls = gr.Number(label="Number of API calls", value=100, precision=0)

        # 3) Load model pricing externally from JSON
        # Ensure model_pricing.json is in the same folder or specify a path
        pricing_json_path = os.path.join(os.path.dirname(__file__), "model_pricing.json")
        with open(pricing_json_path, "r") as f:
            MODEL_PRICING = json.load(f)

        # Build a list of unique providers, add "All"
        unique_providers = sorted(list({row["provider"] for row in MODEL_PRICING}))
        provider_selector = gr.Dropdown(
            label="Provider",
            choices=["All"] + unique_providers,
            value="All"
        )

        # Let user type a model substring
        model_search_box = gr.Textbox(
            label="Model search substring",
            placeholder="Type part of model name if you want to filter (e.g. '4o')",
            value=""
        )

        # Output: table + cost chart
        pricing_output = gr.Dataframe(label="Pricing Table")
        cost_plot = gr.Plot(label="Cost Comparison")

        def compute_pricing(calc_by, in_tokens, out_tokens, calls, provider_filter, model_search):
            """
            1) Possibly convert from words/characters -> tokens
            2) Filter MODEL_PRICING by provider, model substring
            3) Calculate cost for each row, produce a DataFrame
            """
            if in_tokens is None:
                in_tokens = 0
            if out_tokens is None:
                out_tokens = 0
            if calls is None:
                calls = 0

            # Step A: convert from words or characters
            if calc_by == "Words":
                # e.g. approx 1.33 tokens per word
                in_tokens *= 1.33
                out_tokens *= 1.33
            elif calc_by == "Characters":
                # e.g. 4 chars = 1 token
                in_tokens /= 4
                out_tokens /= 4

            # Step B: filter by provider if not "All", and model substring if not empty
            filtered_rows = []
            for row in MODEL_PRICING:
                # match provider?
                if provider_filter != "All" and row["provider"] != provider_filter:
                    continue
                # match model substring?
                if model_search:
                    # case-insensitive substring check
                    if model_search.lower() not in row["model"].lower():
                        continue
                filtered_rows.append(row)

            # Step C: compute cost
            results = []
            for row in filtered_rows:
                provider = row["provider"]
                model = row["model"]
                input_price_1m = row["input_price_1m"]
                output_price_1m = row["output_price_1m"]

                cost_in = (in_tokens / 1_000_000) * input_price_1m
                cost_out = (out_tokens / 1_000_000) * output_price_1m
                price_per_api_call = cost_in + cost_out
                total_price = price_per_api_call * calls

                results.append({
                    "Provider": provider,
                    "Model": model,
                    "Price per API call (USD)": f"{price_per_api_call:.4f}",
                    "Total Price (USD)": f"{total_price:.2f}"
                })

            df = pd.DataFrame(results)
            return df

        def refresh_pricing(
            calc_by, in_tokens, out_tokens, calls,
            provider_filter, model_search
        ):
            """
            1) compute_pricing
            2) build bar chart from total price
            """
            df = compute_pricing(
                calc_by, in_tokens, out_tokens, calls,
                provider_filter, model_search
            )
            if df.empty:
                return df, None

            # We'll parse out numeric from "Total Price (USD)"
            df_numeric = df.copy()
            df_numeric["TotalPriceFloat"] = df_numeric["Total Price (USD)"].apply(lambda x: float(x))
            fig = px.bar(
                df_numeric,
                x="Model",
                y="TotalPriceFloat",
                color="Provider",
                title="Total Price by Model",
                labels={"TotalPriceFloat":"Total Price ($)"},
                text="TotalPriceFloat"
            )
            fig.update_traces(textposition="outside")

            return df, fig

        # We call refresh_pricing whenever any input changes
        inputs = [
            calc_by_selector,
            input_tokens,
            output_tokens,
            api_calls,
            provider_selector,
            model_search_box
        ]
        for inp in inputs:
            inp.change(
                fn=refresh_pricing,
                inputs=inputs,
                outputs=[pricing_output, cost_plot]
            )
