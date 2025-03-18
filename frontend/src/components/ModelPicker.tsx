import { FormControl, InputLabel, MenuItem, Select } from "@mui/material";
import React from "react";
import { AssistantModel } from "../types/assistantTypes";

interface ModelPickerProps {
    selectedModel?: AssistantModel;
    models: AssistantModel[];
    onModelChange: (model: AssistantModel) => void;
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
            <InputLabel id="model-select-label">Select the Assistant Model</InputLabel>
            <Select
                labelId="model-select-label"
                id="model-select"
                label="Select the Assistant Model"
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
