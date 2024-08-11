import React, {
  useState,
  useEffect,
  useRef,
  ChangeEvent,
  KeyboardEvent,
} from "react";
import axios from "axios";
import {
  Box,
  TextField,
  IconButton,
  List,
  ListItem,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Paper,
  Tooltip,
  Button,
} from "@mui/material";
import { Speaker } from "../types/Speaker";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import SendIcon from "@mui/icons-material/Send";
import "./Chatbot.css";

interface Message {
  sender: "user" | "bot";
  text: string;
  sources?: string[];
}

interface BackendResponse {
  message: string;
  sources?: string[];
  // Add other keys as needed
}

const Chatbot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [selectedSpeaker, setSelectedSpeaker] = useState<Speaker | string>("");
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [initialLoadComplete, setInitialLoadComplete] =
    useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Load chat history from localStorage on mount
  useEffect(() => {
    const savedMessages = localStorage.getItem("chatMessages");
    if (savedMessages) {
      const parsedMessages: Message[] = JSON.parse(savedMessages);
      console.log("Loaded messages from localStorage:", parsedMessages);
      setMessages(parsedMessages);
    }
    setInitialLoadComplete(true);
  }, []);

  // Save chat history to localStorage whenever messages change after the initial load
  useEffect(() => {
    if (initialLoadComplete) {
      console.log("Saving messages to localStorage:", messages);
      localStorage.setItem("chatMessages", JSON.stringify(messages));
    }
  }, [messages, initialLoadComplete]);

  const sendMessage = async () => {
    if (input.trim() === "") return;

    const userMessage: Message = { sender: "user", text: input };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput("");
    setIsTyping(true);

    const chatHistory = updatedMessages.map((msg) => ({
      sender: msg.sender,
      message: msg.text,
    }));

    try {
      console.log("REACT_APP_BACKEND_URL", process.env.REACT_APP_BACKEND_URL);
      const response = await axios.post<BackendResponse>(
        // Load the backend URL from an environment variable if it is set
        process.env.REACT_APP_BACKEND_URL || "http://localhost:8000/chat",
        {
          user_message: input,
          speaker: selectedSpeaker || null,
          chat_history: chatHistory,
        }
      );
      const botMessage: Message = {
        sender: "bot",
        text: response.data.message,
        sources: response.data.sources,
      };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.error("Error sending message", error);
    } finally {
      setIsTyping(false);
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  };

  const handleSpeakerChange = (e: SelectChangeEvent<string>) => {
    setSelectedSpeaker(e.target.value);
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault(); // Prevent default behavior
      sendMessage();
    }
  };

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  const clearChatHistory = () => {
    setMessages([]);
    localStorage.removeItem("chatMessages");
  };

  useEffect(scrollToBottom, [messages]);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "calc(100vh - 64px)", // Subtract AppBar height
        overflow: "hidden",
      }}
    >
      <Paper
        elevation={3}
        sx={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          mb: 2, // Add margin at the bottom to create space for the sticky bar
        }}
      >
        <List
          sx={{
            flex: 1,
            overflowY: "auto",
            padding: 2,
          }}
        >
          {messages.map((msg, index) => (
            <Box key={index} sx={{ marginBottom: "16px" }}>
              <ListItem
                sx={{
                  display: "flex",
                  justifyContent:
                    msg.sender === "user" ? "flex-end" : "flex-start",
                }}
              >
                <Box className={`bubble-content ${msg.sender}`}>
                  <Typography variant="body1">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.text}
                    </ReactMarkdown>
                  </Typography>
                </Box>
              </ListItem>
              {msg.sources && msg.sources.length > 0 && (
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "flex-start",
                    gap: "4px",
                    marginTop: "-12px",
                    marginLeft: "16px",
                  }}
                >
                  {Array.from(new Set(msg.sources)).map((source, i) => (
                    <Tooltip key={i} title={source}>
                      <Button
                        variant="contained"
                        color="secondary"
                        size="small"
                        sx={{
                          minWidth: "24px",
                          padding: "4px",
                          borderRadius: "50%",
                          width: "24px",
                          height: "24px",
                          minHeight: "24px",
                        }}
                        onClick={() => window.open(source, "_blank")}
                      >
                        {i + 1}
                      </Button>
                    </Tooltip>
                  ))}
                </Box>
              )}
            </Box>
          ))}
          {isTyping && (
            <ListItem sx={{ display: "flex", justifyContent: "flex-start" }}>
              <Box className="bubble-content bot typing-indicator">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </Box>
            </ListItem>
          )}
          <div ref={messagesEndRef} />
        </List>
      </Paper>
      <Box
        sx={{
          padding: 2,
          paddingBottom: 3, // Increase bottom padding
          borderTop: "1px solid #ddd",
          backgroundColor: "background.default",
          display: "flex",
          alignItems: "center",
          gap: 2,
          position: "sticky",
          bottom: 0,
          zIndex: 1,
        }}
      >
        <Button
          variant="outlined"
          color="secondary"
          onClick={clearChatHistory}
          size="small"
          sx={{
            whiteSpace: "nowrap",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            flex: 0.5,
            minWidth: "100px",
            height: "56px",
          }}
        >
          Clear Chat
          <br />
          History
        </Button>
        <FormControl sx={{ flex: 1 }}>
          <InputLabel id="speaker-select-label">Filter by Speaker</InputLabel>
          <Select
            labelId="speaker-select-label"
            value={selectedSpeaker}
            onChange={handleSpeakerChange}
            label="Filter by Speaker"
          >
            <MenuItem value="">None</MenuItem>
            {Object.values(Speaker).map((speaker) => (
              <MenuItem key={speaker} value={speaker}>
                {speaker}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Box sx={{ display: "flex", alignItems: "center", flex: 4 }}>
          <TextField
            fullWidth
            value={input}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
          />
          <IconButton color="primary" onClick={sendMessage} sx={{ ml: 1 }}>
            <SendIcon />
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
};

export default Chatbot;
