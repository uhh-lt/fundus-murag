import {
    Alert,
    Box,
    Button,
    Card,
    CardActionArea,
    CircularProgress,
    Divider,
    Link,
    Modal,
    Typography,
} from "@mui/material";
import React, { useEffect, useState } from "react";
import { useAgentService } from "../../hooks/useLookupService";
import { FundusCollection } from "../../types/fundusTypes";

// Component to render a FundusCollection
interface FundusCollectionCardProps {
    muragId: string;
}

const FundusCollectionCard: React.FC<FundusCollectionCardProps> = ({ muragId }) => {
    const [collection, setCollection] = useState<FundusCollection | undefined>(undefined);
    const [loading, setLoading] = useState<boolean>(true);
    const [modalOpen, setModalOpen] = useState<boolean>(false);
    const { getFundusCollection } = useAgentService();

    useEffect(() => {
        const fetchCollectionData = async () => {
            try {
                const data = await getFundusCollection(muragId);
                if (data) {
                    setCollection(data);
                }
            } catch (error) {
                console.error("Error fetching collection:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchCollectionData();
    }, [muragId, getFundusCollection]);

    const handleOpenModal = () => {
        setModalOpen(true);
    };

    const handleCloseModal = () => {
        setModalOpen(false);
    };

    if (loading) {
        return (
            <Box sx={{ display: "flex", justifyContent: "center", p: 2 }}>
                <CircularProgress size={40} />
            </Box>
        );
    }

    if (!collection) {
        return (
            <Alert severity="error">
                FUNDus Collection Not Found
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
                width: { xs: "90%", sm: "80%", md: "70%" },
                maxHeight: "90vh",
                bgcolor: "background.paper",
                borderRadius: 2,
                boxShadow: 24,
                p: 4,
                overflow: "auto",
            }}
        >
            <Typography variant="h5" fontWeight="bold">
                {collection.title}
            </Typography>
            <Typography variant="h6" color="text.secondary">
                {collection.title_de}
            </Typography>
            <Divider sx={{ my: 2 }} />

            <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" fontWeight="bold">
                    Collection Details
                </Typography>
                <Box sx={{ ml: 2 }}>
                    <Typography>
                        <strong>Collection Name:</strong> {collection.collection_name}
                    </Typography>
                    <Typography>
                        <strong>MuRAG ID:</strong> {collection.murag_id}
                    </Typography>
                </Box>
            </Box>

            {collection.description && (
                <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                        Description
                    </Typography>
                    <Box sx={{ ml: 2 }}>
                        <Typography>{collection.description}</Typography>
                    </Box>
                </Box>
            )}

            {collection.description_de && (
                <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                        Description (DE)
                    </Typography>
                    <Box sx={{ ml: 2 }}>
                        <Typography>{collection.description_de}</Typography>
                    </Box>
                </Box>
            )}

            {/* Display contact information if available */}
            {collection.contacts && collection.contacts.length > 0 && (
                <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                        Contact Information
                    </Typography>
                    {collection.contacts.map((contact, index) => (
                        <Box key={index} sx={{ ml: 2, mb: 1 }}>
                            <Typography>{contact.contact_name}</Typography>
                            {contact.institution && <Typography>{contact.institution}</Typography>}
                            {contact.email && (
                                <Typography>
                                    <Link href={`mailto:${contact.email}`}>{contact.email}</Link>
                                </Typography>
                            )}
                        </Box>
                    ))}
                </Box>
            )}

            <Divider sx={{ my: 2 }} />
            <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
                <Button variant="outlined" onClick={handleCloseModal}>
                    Close
                </Button>
            </Box>
        </Box>
    );

    // Simplified card (shown in chat)
    return (
        <>
            <Card
                sx={{
                    borderRadius: 2,
                    p: 2,
                    my: 2,
                    cursor: "pointer",
                }}
                onClick={handleOpenModal}
            >
                <CardActionArea>
                    <Typography variant="h6" fontWeight="bold">
                        {collection.title}
                    </Typography>

                    <Divider sx={{ my: 1 }} />

                    <Typography variant="subtitle1">
                        {(collection.description || collection.description_de)?.substring(0, 250) + "..."}
                    </Typography>

                    <Typography variant="subtitle2" color="text.secondary">
                        MuRAG ID: {collection.murag_id}
                    </Typography>

                    <Typography
                        sx={{
                            fontStyle: "italic",
                            fontSize: "small",
                            mt: 1,
                            textAlign: "center",
                        }}
                    >
                        Click to view all details
                    </Typography>
                </CardActionArea>
            </Card>

            {/* Modal with full details */}
            <Modal
                open={modalOpen}
                onClose={handleCloseModal}
                aria-labelledby="collection-modal-title"
                aria-describedby="collection-modal-description"
            >
                {modalContent}
            </Modal>
        </>
    );
};

export default FundusCollectionCard;
