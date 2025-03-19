import { FormControl, InputLabel, MenuItem, Select } from "@mui/material";
import React from "react";
import { AgentModel } from "../types/agentTypes";

interface ModelPickerProps {
    selectedModel?: AgentModel;
    models: AgentModel[];
    onModelChange: (model: AgentModel) => void;
    isLoading: boolean;
    isError: boolean;
}

const ModelPicker: React.FC<ModelPickerProps> = ({ selectedModel, models, onModelChange }) => {
    const handleChange = (event: { target: { value: string } }) => {
        const selectedModel = models.find((model) => model.name === event.target.value);
        if (selectedModel) {
            onModelChange(selectedModel);
        }
    };

    return (
        <FormControl fullWidth sx={{ m: 1 }}>
            <InputLabel id="model-select-label">Select the Agent Model</InputLabel>
            <Select
                labelId="model-select-label"
                id="model-select"
                label="Select the Agent Model"
                value={selectedModel?.name || ""}
                onChange={handleChange}
            >
                {models.map((model) => (
                    <MenuItem key={model.name} value={model.name}>
                        {model.display_name}
                    </MenuItem>
                ))}
            </Select>
        </FormControl>
    );
};

export default ModelPicker;
