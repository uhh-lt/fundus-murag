import {
    Alert,
    Box,
    Button,
    Card,
    CardActionArea,
    CardActions,
    CardContent,
    CardMedia,
    CircularProgress,
    Divider,
    Link,
    Modal,
    Tooltip,
    Typography,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import React, { useEffect, useState } from "react";
import { useAssistantService } from "../../hooks/useLookupService";
import { FundusRecord, FundusRecordImage } from "../../types/fundusTypes";

interface FundusRecordCardProps {
    muragId: string;
}

const FundusRecordCard: React.FC<FundusRecordCardProps> = ({ muragId }) => {
    const [record, setRecord] = useState<FundusRecord | undefined>(undefined);
    const [image, setImage] = useState<FundusRecordImage | undefined>(undefined);
    const [loading, setLoading] = useState<boolean>(true);
    const [modalOpen, setModalOpen] = useState<boolean>(false);
    const [imageLoaded, setImageLoaded] = useState(false);
    const { getFundusRecord, getFundusRecordImage } = useAssistantService();

    useEffect(() => {
        const fetchRecordData = async () => {
            try {
                const recordData = await getFundusRecord(muragId);
                if (recordData) {
                    setRecord(recordData);
                    const imageData = await getFundusRecordImage(muragId);
                    if (imageData) {
                        setImage(imageData);
                    }
                }
            } catch (error) {
                console.error("Error fetching record:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchRecordData();
    }, [muragId, getFundusRecord, getFundusRecordImage]);

    const handleOpenModal = () => {
        setModalOpen(true);
    };

    const handleCloseModal = () => {
        setModalOpen(false);
    };

    if (loading) {
        return (
            <Box sx={{ display: "flex", justifyContent: "center", p: 2 }}>
                <CircularProgress size={20} />
            </Box>
        );
    }

    if (!record) {
        return (
            <Alert severity="error">
                FUNDus Record Not Found
                <Typography>ID: {muragId}</Typography>
            </Alert>
        );
    }

    // Modal content with all details
    const modalContent = (
        <Box
            sx={{
                position: "absolute",
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%)",
                width: { xs: "90%", sm: "80%", md: "50%", lg: "60%", xl: "50%" },
                maxHeight: "90vh",
                bgcolor: "background.paper",
                borderRadius: 2,
                boxShadow: 24,
                p: 4,
                overflow: "auto",
            }}
        >
            <Typography variant="h5" fontWeight="bold">
                {record.title}
            </Typography>
            <Divider sx={{ my: 2 }} />

            <Grid container spacing={2}>
                {/* Record image column */}
                {image && image.base64_image && (
                    <Grid size={12} sx={{ textAlign: "center" }}>
                        <Tooltip title="Click to view in FUNDus!">
                            <Link
                                href={`https://www.fundus.uni-hamburg.de/en/collection_records/${record.fundus_id}`}
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                <Box sx={{ position: "relative", display: "inline-block" }}>
                                    {!imageLoaded && (
                                        <CircularProgress
                                            size={100}
                                            sx={{
                                                position: "absolute",
                                                top: "50%",
                                                left: "50%",
                                                transform: "translate(-50%, -50%)",
                                            }}
                                        />
                                    )}
                                    <img
                                        src={`https://media.fdm.uni-hamburg.de/iiif/3/${record.collection_name}%2F${record.image_name}/full/800,/0/default.jpg`}
                                        alt={record.title}
                                        style={{
                                            maxWidth: "100%",
                                            maxHeight: "40vh",
                                            borderRadius: 4,
                                            display: imageLoaded ? "block" : "none",
                                        }}
                                        onLoad={() => setImageLoaded(true)}
                                    />
                                </Box>
                            </Link>
                        </Tooltip>
                    </Grid>
                )}

                <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                        Basic Information
                    </Typography>
                    <Typography>
                        <strong>Collection:</strong> {record.collection_name}
                    </Typography>
                    <Typography>
                        <strong>FUNDus ID:</strong> {record.fundus_id}
                    </Typography>
                    <Typography>
                        <strong>Catalog No:</strong> {record.catalogno}
                    </Typography>
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                        Additional Details
                    </Typography>
                    {Object.entries(record.details).map(([key, value]) => (
                        <Typography key={key}>
                            <strong>{key}:</strong> {value}
                        </Typography>
                    ))}
                </Grid>

                <Grid size={12}>
                    <Button variant="contained" sx={{ width: "100%" }} onClick={handleCloseModal}>
                        Close
                    </Button>
                </Grid>
            </Grid>
        </Box>
    );

    return (
        <>
            <Card
                sx={{
                    display: "flex",
                    flexDirection: "column",
                    maxWidth: 350,
                    minWidth: 350,
                    maxHeight: 350,
                    minHeight: 350,
                    my: 2,
                }}
                elevation={5}
                onClick={handleOpenModal}
            >
                <CardActionArea>
                    <CardMedia
                        component="img"
                        height="150"
                        image={`data:image/jpeg;base64,${image?.base64_image}`}
                        alt={record.title}
                    />
                    <CardContent>
                        <Typography gutterBottom variant="body1" fontWeight="bold" component="div">
                            {record.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            {record.collection_name}
                        </Typography>
                    </CardContent>
                </CardActionArea>
                <CardActions sx={{ mt: "auto" }}>
                    <Button size="small" color="primary" onClick={handleOpenModal} startIcon="👀">
                        View Details
                    </Button>
                    <Button
                        size="small"
                        color="primary"
                        href={`https://www.fundus.uni-hamburg.de/en/collection_records/${record.fundus_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        startIcon="🔗"
                    >
                        View on FUNDus!
                    </Button>
                </CardActions>
            </Card>

            {/* Modal with full details */}
            <Modal
                open={modalOpen}
                onClose={handleCloseModal}
                aria-labelledby="record-modal-title"
                aria-describedby="record-modal-description"
            >
                {modalContent}
            </Modal>
        </>
    );
};

export default FundusRecordCard;
